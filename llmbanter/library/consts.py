import pkg_resources

package_name = "llmbanter"
version = pkg_resources.get_distribution(package_name).version
success_code = 0

default_output_folder = "./_output/"
default_cache_folder_mp3 = "./.cache/mp3"
default_cache_folder_llm = "./.cache/llm"

# https://platform.openai.com/docs/api-reference/chat/create
default_llm_model = "gpt-3.5-turbo"
default_llm_temperature = 0.7  # Default 1 as per OpenAI docs
default_llm_top_p = 1  # Default 1 as per OpenAI docs

# Models
# gpt-3.5-turbo (short, older)
# gpt-3.5-turbo-1106 (longer, newer)
# gpt-4-1106-preview
