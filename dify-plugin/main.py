from dify_plugin import DifyPluginEnv, Plugin

# Generations can wait up to 420 seconds for a result, under Dify's default
# PLUGIN_MAX_EXECUTION_TIMEOUT of 600 seconds.
plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=600))

if __name__ == "__main__":
    plugin.run()
