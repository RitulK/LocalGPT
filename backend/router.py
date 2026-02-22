import re
from typing import Optional, Dict, Tuple
from enum import Enum


class QuestionType(Enum):
    """Types of questions/prompts the router can detect"""
    INSTRUCTION = "instruction"
    QA = "qa"
    DEBUGGING = "debugging"
    WRITING = "writing"
    TRANSLATION = "translation"
    CODING = "coding"
    REASONING = "reasoning"
    GENERAL = "general"


class ModelRouter:
    """
    Advanced intelligent model router using scoring system
    Analyzes prompts and selects the best model based on multiple criteria
    """
    
    # Model Capability Registry - Define strengths of each model
    MODEL_CAPABILITIES = {
        "qwen2.5-coder:7b": {
            "speed": 7,          # Response speed (1-10)
            "reasoning": 7,      # Logical reasoning ability
            "coding": 10,        # Code generation/debugging
            "context": 8,        # Context understanding
            "writing": 6,        # Creative/technical writing
            "translation": 5,    # Language translation
            "general": 7,        # General conversation
        },
        "qwen:4b": {
            "speed": 9,          # Faster due to smaller size
            "reasoning": 6,      # Good reasoning
            "coding": 7,         # Decent coding ability
            "context": 8,        # Good context understanding
            "writing": 8,        # Better at writing
            "translation": 7,    # Better translation
            "general": 9,        # Excellent general purpose
        }
    }
    
    # Regex patterns for code detection
    CODE_PATTERNS = [
        r'```[\w]*\n[\s\S]*?```',           # Code blocks with syntax
        r'`[^`]+`',                          # Inline code
        r'\b(def|class|function|var|let|const|import|export)\s+\w+',  # Function/class declarations
        r'\b(if|else|for|while|switch|case)\s*\(',  # Control structures
        r'[{}\[\]();]',                      # Common code syntax
        r'\b(return|print|console\.log|echo)\s*\(',  # Common statements
        r'[=+\-*/<>!&|]{2,}',               # Operators
        r'\.(map|filter|reduce|forEach|push|pop)\(',  # Method calls
        r'^\s*[\w]+\s*=\s*.+$',             # Variable assignments (multiline)
    ]
    
    # Keywords for different task types
    CODING_KEYWORDS = [
        "code", "function", "class", "method", "debug", "error", "bug", "fix",
        "python", "javascript", "java", "c++", "typescript", "rust", "go",
        "programming", "algorithm", "syntax", "compile", "runtime", "exception",
        "implement", "script", "api", "endpoint", "database", "sql", "query",
        "html", "css", "react", "vue", "angular", "node", "django", "flask",
        "git", "repository", "commit", "merge", "pull request", "refactor",
        "variable", "array", "object", "loop", "conditional", "recursive"
    ]
    
    DEBUGGING_KEYWORDS = [
        "debug", "error", "bug", "fix", "issue", "problem", "not working",
        "crash", "exception", "stack trace", "undefined", "null", "nil",
        "segmentation fault", "memory leak", "timeout", "fail", "broken",
        "wrong", "incorrect", "unexpected", "missing"
    ]
    
    REASONING_KEYWORDS = [
        "analyze", "compare", "evaluate", "explain", "why", "how", "what if",
        "philosophy", "theory", "reasoning", "logic", "argument", "prove",
        "scientific", "research", "study", "evidence", "cause", "effect",
        "conclude", "deduce", "infer", "implications", "consequences",
        "understand", "interpret", "assess", "examine"
    ]
    
    WRITING_KEYWORDS = [
        "write", "story", "creative", "poem", "fiction", "character", "essay",
        "narrative", "blog", "article", "content", "draft", "compose",
        "letter", "email", "report", "documentation", "summary", "paragraph",
        "introduction", "conclusion", "outline"
    ]
    
    TRANSLATION_KEYWORDS = [
        "translate", "translation", "language", "convert", "english", "spanish",
        "french", "german", "chinese", "japanese", "in", "to", "from"
    ]
    
    QA_PATTERNS = [
        r'^\s*(?:what|who|where|when|why|how|which|can|could|would|should|is|are|do|does)\s',
        r'\?$',  # Ends with question mark
    ]
    
    INSTRUCTION_PATTERNS = [
        r'^\s*(?:please|kindly|could you|can you|help me|show me|tell me|give me)',
        r'^\s*(?:create|make|build|generate|produce|design|develop)',
        r'^\s*(?:explain|describe|list|show|demonstrate)',
    ]
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.code_regex = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in self.CODE_PATTERNS]
        self.qa_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.QA_PATTERNS]
        self.instruction_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.INSTRUCTION_PATTERNS]
        
        # Default models
        self.default_general = "qwen:4b"
        self.default_coding = "qwen2.5-coder:7b"
        self.default_reasoning = "qwen:4b"
    
    def route(self, prompt: str, settings=None) -> str:
        """
        Route the prompt to the most appropriate model using scoring system
        
        Args:
            prompt: User's input prompt
            settings: Application settings with model preferences
        
        Returns:
            Name of the selected model
        """
        # Detect question type
        question_type = self._detect_question_type(prompt)
        
        # Calculate scores for each model
        scores = self._calculate_model_scores(prompt, question_type)
        
        # Select model with highest score
        best_model = max(scores.items(), key=lambda x: x[1])[0]
        
        return best_model
    
    def _detect_question_type(self, prompt: str) -> QuestionType:
        """
        Detect the type of question/task from the prompt
        
        Args:
            prompt: User's input prompt
        
        Returns:
            QuestionType enum
        """
        prompt_lower = prompt.lower()
        
        # Check for debugging (high priority)
        if self._keyword_match(prompt_lower, self.DEBUGGING_KEYWORDS, threshold=1):
            return QuestionType.DEBUGGING
        
        # Check for code presence
        if self._detect_code(prompt):
            return QuestionType.CODING
        
        # Check for translation
        if self._keyword_match(prompt_lower, self.TRANSLATION_KEYWORDS, threshold=2):
            return QuestionType.TRANSLATION
        
        # Check for writing tasks
        if self._keyword_match(prompt_lower, self.WRITING_KEYWORDS, threshold=1):
            return QuestionType.WRITING
        
        # Check for Q&A pattern
        if any(regex.search(prompt_lower) for regex in self.qa_regex):
            return QuestionType.QA
        
        # Check for instruction pattern
        if any(regex.search(prompt_lower) for regex in self.instruction_regex):
            return QuestionType.INSTRUCTION
        
        # Check for reasoning keywords
        if self._keyword_match(prompt_lower, self.REASONING_KEYWORDS, threshold=2):
            return QuestionType.REASONING
        
        # Default to general
        return QuestionType.GENERAL
    
    def _detect_code(self, prompt: str) -> bool:
        """
        Detect if prompt contains code using regex patterns
        
        Args:
            prompt: User's input prompt
        
        Returns:
            True if code is detected
        """
        # Check for code blocks or code-like patterns
        for regex in self.code_regex:
            if regex.search(prompt):
                return True
        
        # Check for coding keywords with high density
        prompt_lower = prompt.lower()
        if self._keyword_match(prompt_lower, self.CODING_KEYWORDS, threshold=2):
            return True
        
        return False
    
    def _keyword_match(self, text: str, keywords: list, threshold: int = 1) -> bool:
        """
        Check if text contains keywords above threshold
        
        Args:
            text: Text to check (lowercase)
            keywords: List of keywords
            threshold: Minimum number of matches needed
        
        Returns:
            True if threshold is met
        """
        count = 0
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                count += 1
                if count >= threshold:
                    return True
        return False
    
    def _calculate_model_scores(self, prompt: str, question_type: QuestionType) -> Dict[str, float]:
        """
        Calculate scores for each available model
        
        Args:
            prompt: User's input prompt
            question_type: Detected question type
        
        Returns:
            Dictionary mapping model names to scores
        """
        scores = {}
        prompt_lower = prompt.lower()
        prompt_length = len(prompt.split())
        
        for model_name, capabilities in self.MODEL_CAPABILITIES.items():
            score = 0.0
            
            # Base score from question type capability match
            if question_type == QuestionType.CODING:
                score += capabilities["coding"] * 3.0
            elif question_type == QuestionType.DEBUGGING:
                score += capabilities["coding"] * 2.5
                score += capabilities["reasoning"] * 1.5
            elif question_type == QuestionType.WRITING:
                score += capabilities["writing"] * 3.0
            elif question_type == QuestionType.TRANSLATION:
                score += capabilities["translation"] * 3.0
            elif question_type == QuestionType.REASONING:
                score += capabilities["reasoning"] * 3.0
            elif question_type == QuestionType.QA:
                score += capabilities["general"] * 2.0
                score += capabilities["reasoning"] * 1.0
            elif question_type == QuestionType.INSTRUCTION:
                score += capabilities["general"] * 2.0
            else:  # GENERAL
                score += capabilities["general"] * 3.0
            
            # Keyword density scoring
            coding_density = self._get_keyword_density(prompt_lower, self.CODING_KEYWORDS)
            reasoning_density = self._get_keyword_density(prompt_lower, self.REASONING_KEYWORDS)
            writing_density = self._get_keyword_density(prompt_lower, self.WRITING_KEYWORDS)
            
            score += coding_density * capabilities["coding"] * 0.5
            score += reasoning_density * capabilities["reasoning"] * 0.5
            score += writing_density * capabilities["writing"] * 0.5
            
            # Code detection bonus
            if self._detect_code(prompt):
                score += capabilities["coding"] * 2.0
            
            # Context length consideration
            if prompt_length > 200:
                score += capabilities["context"] * 0.8
            elif prompt_length > 100:
                score += capabilities["context"] * 0.5
            
            # Speed bonus for short prompts
            if prompt_length < 50:
                score += capabilities["speed"] * 0.5
            
            scores[model_name] = score
        
        return scores
    
    def _get_keyword_density(self, text: str, keywords: list) -> float:
        """
        Calculate keyword density in text
        
        Args:
            text: Text to analyze (lowercase)
            keywords: List of keywords
        
        Returns:
            Density score (0.0 to 1.0)
        """
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        matches = 0
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches += len(re.findall(pattern, text))
        
        # Normalize to 0-1 range
        density = min(matches / max(word_count * 0.1, 1), 1.0)
        return density
    
    def get_routing_reasoning(self, prompt: str, settings=None) -> str:
        """
        Get explanation of model selection
        
        Args:
            prompt: User's input prompt
            settings: Application settings
        
        Returns:
            Human-readable explanation
        """
        question_type = self._detect_question_type(prompt)
        scores = self._calculate_model_scores(prompt, question_type)
        selected_model = max(scores.items(), key=lambda x: x[1])[0]
        
        explanations = {
            QuestionType.CODING: "Detected coding task",
            QuestionType.DEBUGGING: "Detected debugging request",
            QuestionType.WRITING: "Detected writing/creative task",
            QuestionType.TRANSLATION: "Detected translation request",
            QuestionType.REASONING: "Detected analytical/reasoning task",
            QuestionType.QA: "Detected question answering",
            QuestionType.INSTRUCTION: "Detected instruction/command",
            QuestionType.GENERAL: "General conversation"
        }
        
        reason = explanations.get(question_type, "General conversation")
        score_info = f" (score: {scores[selected_model]:.1f})"
        
        return f"{reason} → {selected_model}{score_info}"
    
    def get_all_scores(self, prompt: str) -> Dict[str, float]:
        """
        Get scores for all models (for debugging/analysis)
        
        Args:
            prompt: User's input prompt
        
        Returns:
            Dictionary of model scores
        """
        question_type = self._detect_question_type(prompt)
        return self._calculate_model_scores(prompt, question_type)
