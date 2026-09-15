# frozen_string_literal: true

require 'json'
require 'fileutils'
require 'set'
require 'time'

module Codex
  module Memorial3D
    class Runner
      INCH_TO_M = 0.0254
      TEMP_DIMENSION_TAG = 'CODEX_TEMP_DIMENSIONS'
      TEMP_DIMENSION_MATERIAL = 'CODEX_TEMP_DIMENSION_BLACK'

      def initialize(config_path)
        @config_path = File.expand_path(config_path)
        @config = JSON.parse(File.read(@config_path, encoding: 'UTF-8'))
        @output_dir = File.expand_path(@config.fetch('output_dir'))
        @render_dir = File.join(@output_dir, 'renders')
        @render_queue = []
        @errors = []
        @expanded_component_definitions = Set.new
      end

      def start
        FileUtils.mkdir_p(@render_dir)
        write_status('opening_model')
        @model_wait_attempts = 0
        wait_for_model
      rescue StandardError => error
        fail_job(error)
      end

      private

      def wait_for_model
        source_path = File.expand_path(@config.fetch('model_path')).downcase
        model = Sketchup.active_model
        current_path = model ? File.expand_path(model.path.to_s).downcase : ''
        if !current_path.empty? && current_path == source_path
          UI.start_timer(0.5, false) { extract }
          return
        end

        @model_wait_attempts += 1
        if @model_wait_attempts == 12
          write_status('loading_model')
          status = Sketchup.open_file(
            File.expand_path(@config.fetch('model_path')),
            with_status: true,
            show_version_warning_dialog: false
          )
          raise "SketchUp failed to open model: #{status.inspect}" unless status
        end
        if (@model_wait_attempts % 10).zero?
          File.write(
            File.join(@output_dir, 'status.json'),
            JSON.pretty_generate(
              status: 'opening_model', updated_at: Time.now.iso8601,
              expected_path: source_path, active_path: current_path,
              attempt: @model_wait_attempts
            ),
            mode: 'w:UTF-8'
          )
        end
        raise "Timed out waiting for active model: #{source_path}" if @model_wait_attempts > 240

        UI.start_timer(0.5, false) { wait_for_model }
      rescue StandardError => error
        fail_job(error)
      end

      def extract
        write_status('extracting')
        model = Sketchup.active_model
        manifest = serialize_model(model)
        File.write(File.join(@output_dir, 'manifest.json'), JSON.pretty_generate(manifest), mode: 'w:UTF-8')
        prepare_render_queue(model)
        render_next
      rescue StandardError => error
        fail_job(error)
      end

      def serialize_model(model)
        {
          schema_version: '1.0', extracted_at: Time.now.iso8601,
          source_path: File.expand_path(@config.fetch('model_path')),
          sketchup_version: Sketchup.version,
          model: {
            title: model.title, description: model.description, guid: model.guid,
            bounds: bounds_hash(model.bounds), units: units_hash(model)
          },
          statistics: statistics_hash(model),
          tags: model.layers.map { |layer| layer_hash(layer) },
          materials: model.materials.map { |material| material_hash(material) },
          scenes: model.pages.each_with_index.map { |page, index| scene_hash(page, index) },
          root_tag_summaries: serialize_root_tag_summaries(model.entities),
          root_entities: serialize_entities(model.entities),
          definitions: serialize_definitions(model),
          annotations: collect_annotations(model.entities)
        }
      end

      def units_hash(model)
        options = model.options['UnitsOptions']
        %w[LengthFormat LengthUnit LengthPrecision SuppressUnitsDisplay].to_h do |key|
          [key, safe_option(options, key)]
        end
      end

      def safe_option(options, key)
        options[key]
      rescue StandardError
        nil
      end

      def statistics_hash(model)
        root_types = Hash.new(0)
        model.entities.each { |entity| root_types[entity.typename] += 1 if entity.valid? }
        {
          root_entity_count: model.entities.length,
          root_type_counts: root_types,
          materials: model.materials.length,
          component_definitions: model.definitions.count { |definition| !definition.image? },
          layers: model.layers.length,
          pages: model.pages.length
        }
      rescue StandardError => error
        { error: error.message }
      end

      def serialize_root_tag_summaries(entities)
        entities.group_by { |entity| entity.layer ? entity.layer.name : 'Sem tag' }.map do |tag_name, tagged_entities|
          bounds = Geom::BoundingBox.new
          type_counts = Hash.new(0)
          material_counts = Hash.new(0)
          tagged_entities.each do |entity|
            next unless entity.valid?

            type_counts[entity.typename] += 1
            begin
              bounds.add(entity.bounds)
            rescue StandardError
              # Some helper entities do not expose useful bounds.
            end
            next unless entity.is_a?(Sketchup::Face)

            material = (entity.material || entity.back_material)&.display_name || 'Sem material'
            material_counts[material] += 1
          end
          layer = tagged_entities.first&.layer
          {
            tag: tag_name,
            visible: layer ? layer.visible? : true,
            entity_count: tagged_entities.count(&:valid?),
            type_counts: type_counts,
            bounds: bounds.empty? ? nil : bounds_hash(bounds),
            material_face_counts: material_counts,
            sample_persistent_ids: tagged_entities.select(&:valid?).first(30).map(&:persistent_id)
          }
        end.sort_by { |summary| summary[:tag].to_s.downcase }
      end

      def layer_hash(layer)
        { name: layer.name, visible: layer.visible?, folder: layer.respond_to?(:folder) && layer.folder ? layer.folder.name : nil }
      end

      def material_hash(material)
        color = material.color
        {
          name: material.name, display_name: material.display_name, alpha: material.alpha,
          color_rgb: color ? [color.red, color.green, color.blue] : nil,
          textured: !material.texture.nil?,
          texture_size_m: material.texture ? [to_m(material.texture.width), to_m(material.texture.height)] : nil
        }
      rescue StandardError => error
        { name: material.name, error: error.message }
      end

      def scene_hash(page, index)
        {
          index: index + 1, name: page.name, description: page.description,
          use_camera: page.use_camera?, camera: camera_hash(page.camera)
        }
      rescue StandardError => error
        { index: index + 1, name: page.name, error: error.message }
      end

      def camera_hash(camera)
        return nil unless camera

        {
          eye_m: point_m(camera.eye), target_m: point_m(camera.target), up: vector_array(camera.up),
          perspective: camera.perspective?, fov: camera.fov,
          height_m: camera.respond_to?(:height) ? to_m(camera.height) : nil
        }
      end

      def serialize_entities(entities, transform = Geom::Transformation.new, depth = 0, path = [])
        return [] if depth > Integer(@config.fetch('max_depth', 8))

        entities.filter_map do |entity|
          next unless entity.valid?

          case entity
          when Sketchup::Group, Sketchup::ComponentInstance
            instance_transform = transform * entity.transformation
            label = entity_label(entity)
            data = instance_hash(entity, instance_transform, depth, path + [label])
            definition_key = entity.definition.persistent_id
            if entity.is_a?(Sketchup::ComponentInstance) && @expanded_component_definitions.include?(definition_key)
              data[:children] = []
              data[:children_omitted_reason] = 'definition_already_expanded'
            else
              @expanded_component_definitions.add(definition_key) if entity.is_a?(Sketchup::ComponentInstance)
              data[:children] = serialize_entities(instance_entities(entity), instance_transform, depth + 1, path + [label])
            end
            data
          when Sketchup::Image
            image_name = entity.respond_to?(:name) ? entity.name : File.basename(entity.path.to_s)
            basic_entity_hash(entity).merge(type: 'Image', name: image_name, path: path, bounds: bounds_hash(entity.bounds))
          end
        end
      end

      def instance_hash(entity, world_transform, depth, path)
        definition = entity.definition
        local_bounds = definition.bounds
        scales = [world_transform.xaxis.length, world_transform.yaxis.length, world_transform.zaxis.length]
        # SketchUp's BoundingBox accessors are width=X, height=Y and depth=Z.
        # Store production dimensions consistently as X/Y/Z = L/P/A.
        dimensions = [local_bounds.width, local_bounds.height, local_bounds.depth]
        {
          type: entity.is_a?(Sketchup::Group) ? 'Group' : 'ComponentInstance',
          name: entity.name, definition_name: definition.name, path: path, depth: depth,
          persistent_id: entity.persistent_id, entity_id: entity.entityID,
          guid: entity.respond_to?(:guid) ? entity.guid : nil,
          visible: entity.visible?, hidden: entity.hidden?, locked: entity.locked?,
          tag: entity.layer ? entity.layer.name : nil,
          material: entity.material ? entity.material.display_name : nil,
          world_bounds: bounds_hash(entity.bounds),
          local_dimensions_m: dimensions.zip(scales).map { |dimension, scale| to_m(dimension * scale) },
          transform: world_transform.to_a.map(&:to_f), attributes: attribute_hash(entity)
        }
      end

      def serialize_definitions(model)
        model.definitions.filter_map do |definition|
          next if definition.image? || definition.instances.empty?

          entities = definition.entities
          materials = Hash.new(0)
          entities.grep(Sketchup::Face).each do |face|
            name = (face.material || face.back_material)&.display_name || 'Sem material'
            materials[name] += 1
          end
          {
            name: definition.name, description: definition.description,
            group_definition: definition.group?, instance_count: definition.instances.length,
            bounds: bounds_hash(definition.bounds), face_count: entities.grep(Sketchup::Face).length,
            edge_count: entities.grep(Sketchup::Edge).length, material_face_counts: materials,
            instance_persistent_ids: definition.instances.map(&:persistent_id)
          }
        end
      end

      def collect_annotations(entities, depth = 0, path = [])
        return [] if depth > Integer(@config.fetch('max_depth', 8))

        results = []
        entities.each do |entity|
          next unless entity.valid?

          if entity.is_a?(Sketchup::Text)
            results << basic_entity_hash(entity).merge(type: 'Text', text: entity.text, path: path)
          elsif entity.is_a?(Sketchup::Dimension)
            results << dimension_hash(entity, path)
          elsif entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
            label = entity_label(entity)
            results.concat(collect_annotations(instance_entities(entity), depth + 1, path + [label]))
          end
        end
        results
      end

      def dimension_hash(entity, path)
        data = basic_entity_hash(entity).merge(type: entity.typename, text: entity.respond_to?(:text) ? entity.text : nil, path: path)
        data[:start_m] = point_m(entity.start) if entity.respond_to?(:start)
        data[:end_m] = point_m(entity.end) if entity.respond_to?(:end)
        data[:offset_vector_m] = vector_m(entity.offset_vector) if entity.respond_to?(:offset_vector)
        data
      rescue StandardError => error
        basic_entity_hash(entity).merge(type: entity.typename, path: path, error: error.message)
      end

      def basic_entity_hash(entity)
        { persistent_id: entity.persistent_id, entity_id: entity.entityID, visible: entity.visible?, tag: entity.layer ? entity.layer.name : nil }
      end

      def entity_label(entity)
        name = entity.name.to_s.strip
        name = entity.definition.name.to_s.strip if name.empty?
        name.empty? ? "#{entity.typename}-#{entity.persistent_id}" : name
      end

      def instance_entities(entity)
        entity.is_a?(Sketchup::Group) ? entity.entities : entity.definition.entities
      end

      def attribute_hash(entity)
        dictionaries = entity.attribute_dictionaries
        return {} unless dictionaries

        dictionaries.to_h { |dictionary| [dictionary.name, dictionary.to_h] }
      rescue StandardError
        {}
      end

      def bounds_hash(bounds)
        {
          min_m: point_m(bounds.min), max_m: point_m(bounds.max),
          dimensions_m: [to_m(bounds.width), to_m(bounds.height), to_m(bounds.depth)],
          axis_order: %w[x y z],
          center_m: point_m(bounds.center)
        }
      end

      def point_m(point)
        [to_m(point.x), to_m(point.y), to_m(point.z)]
      end

      def vector_m(vector)
        [to_m(vector.x), to_m(vector.y), to_m(vector.z)]
      end

      def vector_array(vector)
        [vector.x.to_f, vector.y.to_f, vector.z.to_f]
      end

      def to_m(value)
        (value.to_f * INCH_TO_M).round(6)
      end

      def prepare_render_queue(model)
        @render_options = {
          width: Integer(@config.fetch('render_width', 1600)),
          height: Integer(@config.fetch('render_height', 1000)),
          antialias: true, transparent: false, compression: 0.9
        }
        @render_queue << { type: :current, name: '00_modelo_atual' }
        model.pages.first(Integer(@config.fetch('scene_limit', 100))).each_with_index do |page, index|
          @render_queue << { type: :scene, page: page, name: format('%02d_%s', index + 1, safe_filename(page.name)) }
        end
        Array(@config['focus_sets']).each_with_index do |focus, index|
          @render_queue << {
            type: :focus,
            focus: focus,
            name: format('F%02d_%s', index + 1, safe_filename(focus['name']))
          }
        end
      end

      def render_next
        job = @render_queue.shift
        return finish_job unless job

        model = Sketchup.active_model
        delay = 0.35
        if job[:type] == :scene
          model.pages.selected_page = job[:page]
          model.active_view.invalidate
          delay = 2.0
        elsif job[:type] == :focus
          setup_focus_view(model, job[:focus])
          delay = 1.5
        end
        File.write(
          File.join(@output_dir, 'status.json'),
          JSON.pretty_generate(
            status: 'rendering', current: job[:name],
            remaining: @render_queue.length, updated_at: Time.now.iso8601
          ),
          mode: 'w:UTF-8'
        )
        UI.start_timer(delay, false) do
          begin
            force_white_background(model)
            force_vector_style(model, job[:type] == :focus, job[:focus])
            path = File.join(@render_dir, "#{job[:name]}.png")
            options = @render_options.merge(filename: path)
            if job[:type] == :focus
              # Scale viewport-dependent graphics (dimension text, arrows and
              # line weights) for legibility after the render is placed on a
              # memorial page. Geometry and camera framing remain unchanged.
              options[:scale_factor] = @config.fetch('technical_scale_factor', 2.5).to_f
            end
            model.active_view.write_image(options)
          rescue StandardError => error
            @errors << { render: job[:name], error: error.message }
          ensure
            render_next
          end
        end
      rescue StandardError => error
        fail_job(error)
      end

      def force_white_background(model)
        options = model.rendering_options
        white = Sketchup::Color.new(255, 255, 255)

        # Saved scenes can preserve a fixed camera aspect ratio. SketchUp
        # letterboxes that ratio with gray bars when the exported image has a
        # different proportion, which violates the memorial's all-white
        # background rule. Reset only the temporary active camera framing; the
        # source model is closed without saving after extraction.
        camera = model.active_view.camera
        camera.aspect_ratio = 0.0 if camera.respond_to?(:aspect_ratio=)

        {
          'BackgroundColor' => white,
          'SkyColor' => white,
          'GroundColor' => white,
          'DrawGround' => false,
          'DrawHorizon' => false,
          'DisplayFog' => false,
          'DisplayInstanceAxes' => false,
          'DisplaySketchAxes' => false,
          'DisplaySectionPlanes' => false,
          'DisplayWatermarks' => false
        }.each do |key, value|
          options[key] = value if options.keys.include?(key)
        end

        shadow_info = model.shadow_info
        shadow_info['DisplayShadows'] = false if shadow_info.keys.include?('DisplayShadows')
        shadow_info['OnGround'] = false if shadow_info.keys.include?('OnGround')
        model.active_view.invalidate
      end

      def force_vector_style(model, technical_view, focus = nil)
        options = model.rendering_options
        black = Sketchup::Color.new(0, 0, 0)
        settings = {
          'EdgeDisplayMode' => 1,
          'EdgeColorMode' => 0,
          'EdgeColor' => black,
          'EdgeType' => 0,
          'DrawProfilesOnly' => false,
          'DrawSilhouettes' => true,
          'SilhouetteWidth' => focus.is_a?(Hash) ? focus.fetch('silhouette_width', 1).to_i : 1,
          'DrawDepthQue' => false,
          'DrawLineEnds' => false,
          'LineEndWidth' => 0,
          'JitterEdges' => false,
          'ExtendLines' => false,
          'LineExtension' => 0,
          'MaterialTransparency' => false,
          'ModelTransparency' => false,
          'AmbientOcclusion' => false
        }
        if technical_view
          settings['RenderMode'] = focus.is_a?(Hash) ? focus.fetch('render_mode', 2).to_i : 2
          settings['Texture'] = false
        end
        settings.each do |key, value|
          options[key] = value if options.keys.include?(key)
        end
        model.active_view.invalidate
      end

      def setup_focus_view(model, focus)
        clear_temporary_dimensions(model)
        ids = Array(focus['persistent_ids']).map(&:to_i)
        definition_names = Array(focus['definition_names']).map(&:to_s)
        tag_names = Array(focus['tag_names']).map(&:to_s)
        tag_entities = model.entities.select do |entity|
          name = entity.respond_to?(:definition) ? entity.definition.name.to_s : ''
          tag = entity.layer ? entity.layer.name.to_s : ''
          ids.include?(entity.persistent_id) || definition_names.include?(name) || tag_names.include?(tag)
        end
        selected = tag_entities.select { |entity| entity_matches_filter?(entity, focus['center_filter_m']) }
        raise "No root entities found for focus #{focus['name']}" if selected.empty?

        model.selection.clear
        if tag_names.any? && ids.empty? && definition_names.empty?
          dimension_layer = temporary_dimension_layer(model)
          model.active_layer = dimension_layer
          model.layers.each do |layer|
            layer.visible = tag_names.include?(layer.name.to_s) || layer.name.to_s == TEMP_DIMENSION_TAG
          end
          if focus['center_filter_m']
            selected_ids = selected.map(&:persistent_id).to_set
            tag_entities.each { |entity| entity.hidden = !selected_ids.include?(entity.persistent_id) if entity.respond_to?(:hidden=) }
          end
        else
          selected_ids = selected.map(&:persistent_id)
          model.entities.each do |entity|
            next unless entity.respond_to?(:hidden=)

            entity.hidden = !selected_ids.include?(entity.persistent_id)
          end
        end

        bounds = Geom::BoundingBox.new
        selected.each { |entity| bounds.add(entity.bounds) }
        center = bounds.center
        span = [bounds.width, bounds.height, bounds.depth].max
        distance = [span * 1.55, 120.0].max
        lift = [bounds.depth * 0.3, distance * 0.12].max
        direction = focus.fetch('view', 'iso_front')
        eye = case direction
              when 'front' then Geom::Point3d.new(center.x, bounds.min.y - distance, center.z)
              when 'rear' then Geom::Point3d.new(center.x, bounds.max.y + distance, center.z)
              when 'left' then Geom::Point3d.new(bounds.min.x - distance, center.y, center.z)
              when 'right' then Geom::Point3d.new(bounds.max.x + distance, center.y, center.z)
              when 'top' then Geom::Point3d.new(center.x, center.y, bounds.max.z + distance)
              when 'bottom' then Geom::Point3d.new(center.x, center.y, bounds.min.z - distance)
              when 'iso_rear' then Geom::Point3d.new(center.x + distance, center.y + distance, center.z + lift)
              else Geom::Point3d.new(center.x - distance, center.y - distance, center.z + lift)
              end
        up = %w[top bottom].include?(direction) ? Y_AXIS : Z_AXIS
        perspective = focus.fetch('projection', 'perspective') != 'parallel'
        camera = Sketchup::Camera.new(eye, center, up, perspective, 35.0)
        model.active_view.camera = camera
        configure_dimension_units(model)
        add_focus_dimensions(model, selected, bounds, focus)
        model.rendering_options['DisplayDims'] = true if model.rendering_options.respond_to?(:[]=)
        model.active_view.zoom_extents
        model.active_view.zoom(focus.fetch('view_padding_scale', 0.90).to_f)
        model.active_view.invalidate
      end

      def clear_temporary_dimensions(model)
        dimensions = Array(@temporary_dimensions).select(&:valid?)
        model.entities.erase_entities(dimensions) unless dimensions.empty?
        @temporary_dimensions = []
      end

      def entity_matches_filter?(entity, filter)
        return true unless filter.is_a?(Hash)

        center = entity.bounds.center
        values = { 'x' => to_m(center.x), 'y' => to_m(center.y), 'z' => to_m(center.z) }
        filter.all? do |axis, range|
          next true unless values.key?(axis.to_s) && range.is_a?(Array) && range.length == 2

          values[axis.to_s] >= range[0].to_f && values[axis.to_s] <= range[1].to_f
        end
      rescue StandardError
        false
      end

      def add_focus_dimensions(model, selected, union_bounds, focus)
        mode = focus.fetch('dimension_mode', 'union')
        axes = clear_dimension_axes(
          Array(focus.fetch('dimension_axes', %w[width depth height])),
          focus.fetch('view', 'iso_front')
        )
        targets = []
        targets << union_bounds if %w[union union_and_first].include?(mode)
        targets << selected.first.bounds if %w[first union_and_first].include?(mode) && selected.first
        targets.each_with_index do |bounds, index|
          margin = [bounds.width, bounds.height, bounds.depth].max * (0.10 + index * 0.08)
          margin = 12.0 if margin < 12.0
          min = bounds.min
          max = bounds.max
          span = [bounds.width, bounds.height, bounds.depth].max
          min_length = span * focus.fetch('dimension_min_fraction', 0.08).to_f
          view_direction = focus.fetch('view', 'iso_front')
          if axes.include?('width') && bounds.width >= min_length
            offset = %w[front rear].include?(view_direction) ? [0, 0, -margin] : [0, -margin, 0]
            add_dimension(model, [min.x, min.y, min.z], [max.x, min.y, min.z], offset)
          end
          if axes.include?('depth') && bounds.height >= min_length
            offset = %w[left right].include?(view_direction) ? [0, 0, -margin] : [-margin, 0, 0]
            add_dimension(model, [min.x, min.y, min.z], [min.x, max.y, min.z], offset)
          end
          if axes.include?('height') && bounds.depth >= min_length
            offset = %w[left right].include?(view_direction) ? [0, margin, 0] : [margin, 0, 0]
            add_dimension(model, [max.x, min.y, min.z], [max.x, min.y, max.z], offset)
          end
        end
      end

      def clear_dimension_axes(requested_axes, view_direction)
        visible_axes = case view_direction
                       when 'front', 'rear' then %w[width height]
                       when 'left', 'right' then %w[depth height]
                       when 'top', 'bottom' then %w[width depth]
                       else %w[width depth height]
                       end
        requested_axes.map(&:to_s) & visible_axes
      end

      def configure_dimension_units(model)
        units = model.options['UnitsOptions']
        units['LengthFormat'] = 0 if units.keys.include?('LengthFormat')
        units['LengthUnit'] = 4 if units.keys.include?('LengthUnit')
        units['LengthPrecision'] = 2 if units.keys.include?('LengthPrecision')
        units['SuppressUnitsDisplay'] = false if units.keys.include?('SuppressUnitsDisplay')
      rescue StandardError
        nil
      end

      def add_dimension(model, start_point, end_point, offset)
        dimension = model.entities.add_dimension_linear(start_point, end_point, offset)
        dimension.layer = temporary_dimension_layer(model)
        dimension.material = temporary_dimension_material(model)
        dimension.hidden = false if dimension.respond_to?(:hidden=)
        dimension.visible = true if dimension.respond_to?(:visible=)
        @temporary_dimensions ||= []
        @temporary_dimensions << dimension
      end

      def temporary_dimension_material(model)
        material = model.materials[TEMP_DIMENSION_MATERIAL] || model.materials.add(TEMP_DIMENSION_MATERIAL)
        material.color = Sketchup::Color.new(0, 0, 0)
        material
      end

      def temporary_dimension_layer(model)
        @temporary_dimension_layer ||= model.layers[TEMP_DIMENSION_TAG] || model.layers.add(TEMP_DIMENSION_TAG)
        @temporary_dimension_layer.visible = true
        @temporary_dimension_layer
      end

      def safe_filename(name)
        value = name.to_s.encode('UTF-8', invalid: :replace, undef: :replace, replace: '')
        value = value.gsub(/[^0-9A-Za-zÀ-ÿ._-]+/, '_').gsub(/_+/, '_')
        value.empty? ? 'sem_nome' : value[0, 100]
      end

      def finish_job
        File.write(File.join(@output_dir, 'render_errors.json'), JSON.pretty_generate(@errors), mode: 'w:UTF-8')
        write_status('complete')
        close_and_quit
      end

      def fail_job(error)
        FileUtils.mkdir_p(@output_dir) if @output_dir
        payload = { status: 'failed', error_class: error.class.name, message: error.message, backtrace: error.backtrace }
        File.write(File.join(@output_dir || File.dirname(@config_path), 'status.json'), JSON.pretty_generate(payload), mode: 'w:UTF-8')
        close_and_quit
      rescue StandardError
        Sketchup.quit
      end

      def write_status(status)
        FileUtils.mkdir_p(@output_dir)
        File.write(File.join(@output_dir, 'status.json'), JSON.pretty_generate(status: status, updated_at: Time.now.iso8601), mode: 'w:UTF-8')
      end

      def close_and_quit
        model = Sketchup.active_model
        model.close(true) if model
        UI.start_timer(1.0, false) { Sketchup.quit }
      end
    end
  end
end
