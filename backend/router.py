import re
from typing import Optional


class ModelRouter:
    """
    Intelligent model router that selects the best model based on the prompt
    """
    
    # Keywords that indicate different types of tasks
    CODING_KEYWORDS = [
        "code", "function", "class", "debug", "error", "python", "javascript",
        "java", "c++", "programming", "algorithm", "syntax", "compile",
        "implement", "script", "api", "database", "sql", "html", "css",
        "react", "node", "django", "flask", "git", "repository", "bug"
    ]
    
    REASONING_KEYWORDS = [
        "analyze", "compare", "evaluate", "explain", "why", "how",
        "philosophy", "theory", "reasoning", "logic", "argument",
        "scientific", "research", "study", "evidence", "cause",
        "effect", "conclude", "deduce", "infer"
    ]
    
    CREATIVE_KEYWORDS = [
        "story", "write", "creative", "poem", "fiction", "character",
        "narrative", "essay", "blog", "article", "content"
    ]
    
    def __init__(self):
        # Default model preferences (can be overridden by settings)
        self.default_general = "qwen:4b"
        self.default_coding = "qwen:4b"
        self.default_reasoning = "qwen:4b"
    
    def route(self, prompt: str, settings=None) -> str:
        """
        Route the prompt to the most appropriate model
        
        Args:
            prompt: User's input prompt
            settings: Application settings with model preferences
        
        Returns:
            Name of the selected model
        """
        prompt_lower = prompt.lower()
        
        # Get model preferences from settings if available
        general_model = self.default_general
        coding_model = self.default_coding
        reasoning_model = self.default_reasoning
        
        if settings:
            general_model = settings.default_general_model or self.default_general
            coding_model = settings.default_coding_model or self.default_coding
            reasoning_model = settings.default_reasoning_model or self.default_reasoning
        
        # Check for coding-related prompts
        if self._contains_keywords(prompt_lower, self.CODING_KEYWORDS):
            return coding_model
        
        # Check for reasoning/analytical prompts
        if self._contains_keywords(prompt_lower, self.REASONING_KEYWORDS):
            return reasoning_model
        
        # Check prompt length - longer prompts might need more capable models
        if len(prompt.split()) > 100:
            return reasoning_model
        
        # Check for code blocks in the prompt
        if "```" in prompt or "def " in prompt or "function " in prompt:
            return coding_model
        
        # Default to general model
        return general_model
    
    def get_routing_reasoning(self, prompt: str, settings=None) -> str:
        """
        Get a human-readable explanation of why a particular model was chosen
        
        Args:
            prompt: User's input prompt
            settings: Application settings
        
        Returns:
            Explanation string
        """
        prompt_lower = prompt.lower()
        
        if self._contains_keywords(prompt_lower, self.CODING_KEYWORDS):
            return "Detected coding-related keywords - using coding model"
        
        if "```" in prompt or "def " in prompt or "function " in prompt:
            return "Detected code block in prompt - using coding model"
        
        if self._contains_keywords(prompt_lower, self.REASONING_KEYWORDS):
            return "Detected analytical/reasoning keywords - using reasoning model"
        
        if len(prompt.split()) > 100:
            return "Long prompt detected - using reasoning model for complex analysis"
        
        return "General conversation - using default general model"
    
    def _contains_keywords(self, text: str, keywords: list) -> bool:
        """
        Check if text contains any of the specified keywords
        
        Args:
            text: Text to check (should be lowercase)
            keywords: List of keywords to look for
        
        Returns:
            True if any keyword is found
        """
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                return True
        return False
    
    def add_custom_rule(self, keywords: list, model_name: str):
        """
        Add a custom routing rule (for future extensibility)
        
        Args:
            keywords: List of keywords to trigger this rule
            model_name: Model to use when keywords are detected
        """
        # This can be extended to support user-defined routing rules
        pass
