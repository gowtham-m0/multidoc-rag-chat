import os 
import sys
import json
from pathlib import Path

# Add the project root to sys.path to allow absolute imports from multi_doc_chat
sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from multi_doc_chat.utils.config_loader import load_config
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from multi_doc_chat.exceptions.custom_exception import DocumentPortalException
from langchain_ollama import OllamaEmbeddings


class ApiKeyManager:
    REQUIRED_KEYS = ["GROQ_API_KEY", "GOOGLE_API_KEY"]
    
    def __init__(self):
        self.api_keys = {}
        raw = os.getenv("API_KEYS")
        
        if raw:
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed,dict):
                    raise ValueError("Api keys is not a valid json object")
                
                self.api_keys = parsed
                log.info("Loaded API keys from environment variable.")
            except json.JSONDecodeError as e:
                log.warning(f"Failed to parse API_KEYS env variable: {e}")
                
        for key in self.REQUIRED_KEYS:
            if not self.api_keys.get(key):
                env_val = os.getenv(key)
                if env_val:
                    self.api_keys[key] = env_val
                    log.info(f"Loaded {key} from environment variable.")
                else:
                    log.warning(f"{key} not found in API_KEYS or environment variables.")
        
        missing = [k for k in self.REQUIRED_KEYS if not self.api_keys.get(k)]
        if missing:
            log.error(f"Missing required API keys: {missing}")
            raise DocumentPortalException(f"Missing required API keys: {missing}",sys)
        
        log.info("All required API keys loaded successfully.")
        
    def get(self,key:str) -> str:
        val = self.api_keys.get(key)
        if not val: 
            raise KeyError(f"API key '{key}' not found.")
        
        return val
    

class ModelLoader:
    """
        Loads embedding models and LLms based on config and environment.
    """
    
    def __init__(self):
        if os.getenv("ENV","local").lower() != "production":
            load_dotenv(override=True)
            log.info ("Loaded environment variables from .env file.")
        else:
            log.info("Running in production environment, skipping .env loading.")
        self.api_manager = ApiKeyManager()
        self.config = load_config()
        log.info("YAML config loaded", config_keys=list(self.config.keys()))
        
    def _get_provider_config(self, block_name, env_var, default_provider):
        block = self.config.get(block_name, {})

        provider_key = os.getenv(env_var, default_provider)

        if provider_key not in block:
            raise DocumentPortalException(
                f"{block_name} provider '{provider_key}' not found in config.",
                sys
            )

        return block[provider_key]
        
    def load_embedding_model(self):
        """
        loads and return google embeding model from google generative ai
        """
        try:
            config = self._get_provider_config(
                block_name="embedding_model",
                env_var="EMBEDDING_PROVIDER",
                default_provider="ollama"
            )
            
            provider = config.get("provider")
            model_name = config.get("model_name")
            
            log.info(f"Loading embedding model: {model_name}")
            
            providers = {
                "google": lambda: GoogleGenerativeAIEmbeddings(
                    model=model_name,
                    api_key=self.api_manager.get("GOOGLE_API_KEY")
                ),

                "ollama": lambda: OllamaEmbeddings(
                    model=model_name
                )
            }
            
            if provider in providers:
                return providers[provider]()
            else:
                log.error(f"Unsupported embedding provider: {provider}")
                raise DocumentPortalException(f"Unsupported embedding provider: {provider}", sys)
            
        except Exception as e:
            log.error(f"Failed to load embedding model: {e}")
            raise DocumentPortalException(f"Failed to load embedding model: {e}", sys)
    
    def load_llm(self):
        """
        loads and return llm based on config
        """
        config = self._get_provider_config(
            block_name="llm",
            env_var="LLM_PROVIDER",
            default_provider="groq"
        )
        
        provider = config.get("provider")
        model_name = config.get("model_name")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 2048)
        
        log.info(f"Loading LLM: provider={provider}, model={model_name}")
        
        providers = {
            "google": lambda: ChatGoogleGenerativeAI(
                model = model_name,
                google_api_key = self.api_manager.get("GOOGLE_API_KEY"),
                temperature = temperature,
                max_tokens = max_tokens
            ),
            "groq": lambda: ChatGroq(
                model = model_name,
                api_key = self.api_manager.get("GROQ_API_KEY"),
                temperature = temperature
            )
        }
        if provider in providers:
            return providers[provider]()
        else:
            log.error(f"Unsupported LLM provider: {provider}")
            raise DocumentPortalException(f"Unsupported LLM provider: {provider}", sys)
        
    
    
if __name__ == "__main__":
    loader = ModelLoader()
    
    embeddings = loader.load_embedding_model()
    print(f"Loaded embedding model: {embeddings}")
    result = embeddings.embed_query("Hello, how are you?")
    print(f"Embedding result for 'Hello, how are you?': {result}")
    
    llm = loader.load_llm()
    print(f"Loaded LLM: {llm}")
    result = llm.invoke("What is the capital of France?")
    print(f"LLM response for 'What is the capital of France?': {result}")
