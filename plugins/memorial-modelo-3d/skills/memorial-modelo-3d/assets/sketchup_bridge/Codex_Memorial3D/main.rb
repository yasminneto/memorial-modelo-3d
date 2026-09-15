# frozen_string_literal: true

require 'sketchup.rb'
require File.join(__dir__, 'runner')

module Codex
  module Memorial3D
    STARTUP_PREFIX = 'CodexMemorial3D:Job:' unless const_defined?(:STARTUP_PREFIX)
    PENDING_JOB = File.join(__dir__, 'pending_job.json')

    def self.start_job
      argument = ARGV.empty? ? '' : ARGV.first.to_s
      config_path = if argument.start_with?(STARTUP_PREFIX)
                      argument[STARTUP_PREFIX.length..].to_s.strip
                    elsif File.exist?(PENDING_JOB)
                      claimed = File.join(__dir__, "claimed_job_#{Process.pid}.json")
                      File.rename(PENDING_JOB, claimed)
                      claimed
                    end
      return unless config_path

      config = JSON.parse(File.read(config_path, encoding: 'UTF-8'))
      raise 'Layout jobs are not supported by this portable bridge' if config['job_type'] == 'layout_memorial'
      runner = Runner.new(config_path)
      File.delete(config_path) if File.basename(config_path).start_with?('claimed_job_')
      UI.start_timer(0.2, false) { runner.start }
    end

    start_job
  end
end
