import pkg_resources

package_name = "llmvsllm"
version = pkg_resources.get_distribution(package_name).version

default_output_folder = "./_output/"

# https://platform.openai.com/docs/api-reference/chat/create
default_llm_use_localhost = 0
default_llm_model = "gpt-3.5-turbo"
default_llm_temperature = 1  # Default 1 as per OpenAI docs
default_llm_top_p = 1  # Default 1 as per OpenAI docs

# Models
# gpt-3.5-turbo (short, older)
# gpt-3.5-turbo-1106 (longer, newer)
# gpt-4-1106-preview
