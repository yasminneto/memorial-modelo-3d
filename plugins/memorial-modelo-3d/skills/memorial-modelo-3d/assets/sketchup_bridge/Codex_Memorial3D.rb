# frozen_string_literal: true

require 'sketchup.rb'
require 'extensions.rb'

module Codex
  module Memorial3D
    STARTUP_PREFIX = 'CodexMemorial3D:Job:' unless const_defined?(:STARTUP_PREFIX)

    argument = ARGV.empty? ? '' : ARGV.first.to_s
    pending_job = File.join(__dir__, 'Codex_Memorial3D', 'pending_job.json')
    if argument.start_with?(STARTUP_PREFIX) || File.exist?(pending_job)
      begin
        require File.join(__dir__, 'Codex_Memorial3D', 'main')
      rescue StandardError, ScriptError => error
        File.write(
          File.join(__dir__, 'Codex_Memorial3D', 'startup_error.log'),
          "#{error.class}: #{error.message}\n#{Array(error.backtrace).join("\n")}",
          mode: 'w:UTF-8'
        )
        raise
      end
    end

    unless file_loaded?(__FILE__)
      extension = SketchupExtension.new(
        'Codex - Extrator de Memorial',
        File.join('Codex_Memorial3D', 'main')
      )
      extension.description = 'Extrai manifesto técnico e imagens para memoriais descritivos.'
      extension.version = '0.1.0'
      extension.creator = 'Codex'
      extension.copyright = '2026'
      Sketchup.register_extension(extension, true)
      file_loaded(__FILE__)
    end
  end
end
