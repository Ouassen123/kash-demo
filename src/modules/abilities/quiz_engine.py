"""Adaptive quiz engine for abilities assessment."""

import random
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from src.core.logging import get_logger

logger = get_logger(__name__)


class QuestionType(Enum):
    """Types of quiz questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    PATTERN_RECOGNITION = "pattern_recognition"
    LOGICAL_REASONING = "logical_reasoning"
    NUMERICAL_REASONING = "numerical_reasoning"
    VERBAL_REASONING = "verbal_reasoning"


class DifficultyLevel(Enum):
    """Difficulty levels for adaptive questions."""
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


class CognitiveDomain(Enum):
    """Cognitive domains being assessed."""
    MEMORY = "memory"
    ATTENTION = "attention"
    PROCESSING_SPEED = "processing_speed"
    EXECUTIVE_FUNCTION = "executive_function"
    LANGUAGE = "language"
    VISUAL_SPATIAL = "visual_spatial"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVITY = "creativity"


@dataclass
class Question:
    """Quiz question with metadata."""
    id: str
    type: QuestionType
    domain: CognitiveDomain
    difficulty: DifficultyLevel
    question_text: str
    options: List[str] = field(default_factory=list)
    correct_answer: Any = None
    explanation: str = ""
    time_limit_seconds: int = 60
    points_possible: float = 10.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = QuestionType(self.type)
        if isinstance(self.domain, str):
            self.domain = CognitiveDomain(self.domain)
        if isinstance(self.difficulty, str):
            self.difficulty = DifficultyLevel(int(self.difficulty))


@dataclass
class UserResponse:
    """User's response to a question."""
    question_id: str
    user_answer: Any
    response_time_ms: float
    is_correct: bool
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QuizSession:
    """Active quiz session."""
    id: str
    user_id: str
    quiz_type: str
    domain: CognitiveDomain
    questions: List[Question]
    responses: List[UserResponse] = field(default_factory=list)
    current_question_index: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_completed: bool = False
    adaptive_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    
    def get_current_question(self) -> Optional[Question]:
        """Get the current question."""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def get_progress(self) -> float:
        """Get progress as percentage."""
        if not self.questions:
            return 0.0
        return len(self.responses) / len(self.questions)
    
    def get_time_spent(self) -> float:
        """Get time spent in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class AdaptiveAlgorithm:
    """Adaptive difficulty algorithm based on IRT (Item Response Theory)."""
    
    def __init__(self):
        self.ability_estimate = 0.0  # User's ability estimate (theta)
        self.ability_std = 1.0      # Standard deviation of ability
        self.discrimination = 1.0   # Question discrimination parameter
        self.guessing = 0.25        # Guessing parameter for multiple choice
        
    def update_ability(self, question: Question, response: UserResponse) -> float:
        """
        Update user's ability estimate based on response.
        Uses simplified IRT 3-parameter model.
        """
        # Calculate question difficulty (logit scale)
        difficulty = self._difficulty_to_logit(question.difficulty)
        
        # Calculate probability of correct response
        p_correct = self._calculate_probability_correct(difficulty)
        
        # Update ability estimate using Bayesian updating
        if response.is_correct:
            # Increase ability
            update = (1 - p_correct) * self.discrimination
        else:
            # Decrease ability
            update = -p_correct * self.discrimination
        
        # Apply update with learning rate
        learning_rate = 0.3
        self.ability_estimate += learning_rate * update
        
        # Update uncertainty
        self.ability_std *= 0.95  # Reduce uncertainty over time
        
        logger.debug(f"Updated ability: {self.ability_estimate:.3f} (±{self.ability_std:.3f})")
        return self.ability_estimate
    
    def select_next_difficulty(self) -> DifficultyLevel:
        """Select next question difficulty based on current ability."""
        # Map ability to difficulty level
        if self.ability_estimate < -1.5:
            return DifficultyLevel.VERY_EASY
        elif self.ability_estimate < -0.5:
            return DifficultyLevel.EASY
        elif self.ability_estimate < 0.5:
            return DifficultyLevel.MEDIUM
        elif self.ability_estimate < 1.5:
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.VERY_HARD
    
    def _difficulty_to_logit(self, difficulty: DifficultyLevel) -> float:
        """Convert difficulty level to logit scale."""
        mapping = {
            DifficultyLevel.VERY_EASY: -2.0,
            DifficultyLevel.EASY: -1.0,
            DifficultyLevel.MEDIUM: 0.0,
            DifficultyLevel.HARD: 1.0,
            DifficultyLevel.VERY_HARD: 2.0
        }
        return mapping[difficulty]
    
    def _calculate_probability_correct(self, difficulty: float) -> float:
        """Calculate probability of correct response using 3PL IRT model."""
        # 3PL: P(correct) = guessing + (1 - guessing) / (1 + exp(-discrimination * (ability - difficulty)))
        exp_term = math.exp(-self.discrimination * (self.ability_estimate - difficulty))
        probability = self.guessing + (1 - self.guessing) / (1 + exp_term)
        return probability


class QuizEngine:
    """Main quiz engine for adaptive assessments."""
    
    def __init__(self):
        self.question_bank = {}  # domain -> List[Question]
        self.active_sessions = {}  # session_id -> QuizSession
        self.adaptive_algorithms = {}  # session_id -> AdaptiveAlgorithm
        self._load_question_bank()
    
    def create_quiz_session(
        self, 
        user_id: str, 
        quiz_type: str, 
        domain: CognitiveDomain,
        num_questions: int = 20,
        adaptive: bool = True
    ) -> QuizSession:
        """
        Create a new quiz session.
        
        Args:
            user_id: User identifier
            quiz_type: Type of quiz (cognitive, behavioral, technical)
            domain: Cognitive domain to assess
            num_questions: Number of questions in the quiz
            adaptive: Whether to use adaptive difficulty
            
        Returns:
            QuizSession object
        """
        session_id = f"quiz_{user_id}_{datetime.now().timestamp()}"
        
        # Select questions
        if adaptive:
            questions = self._select_adaptive_questions(domain, num_questions)
        else:
            questions = self._select_fixed_questions(domain, num_questions)
        
        session = QuizSession(
            id=session_id,
            user_id=user_id,
            quiz_type=quiz_type,
            domain=domain,
            questions=questions
        )
        
        self.active_sessions[session_id] = session
        
        if adaptive:
            self.adaptive_algorithms[session_id] = AdaptiveAlgorithm()
        
        logger.info(f"Created quiz session {session_id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[QuizSession]:
        """Get quiz session by ID."""
        return self.active_sessions.get(session_id)
    
    def submit_response(
        self, 
        session_id: str, 
        question_id: str, 
        user_answer: Any,
        response_time_ms: float
    ) -> Tuple[bool, Optional[Question]]:
        """
        Submit answer to current question.
        
        Args:
            session_id: Quiz session ID
            question_id: Question being answered
            user_answer: User's answer
            response_time_ms: Time taken to answer
            
        Returns:
            Tuple of (is_correct, next_question)
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.is_completed:
            raise ValueError("Session is already completed")
        
        current_question = session.get_current_question()
        if not current_question or current_question.id != question_id:
            raise ValueError("Invalid question for current state")
        
        # Check answer
        is_correct = self._check_answer(current_question, user_answer)
        
        # Record response
        response = UserResponse(
            question_id=question_id,
            user_answer=user_answer,
            response_time_ms=response_time_ms,
            is_correct=is_correct,
            timestamp=datetime.now()
        )
        
        session.responses.append(response)
        
        # Update adaptive algorithm if enabled
        if session_id in self.adaptive_algorithms:
            algorithm = self.adaptive_algorithms[session_id]
            algorithm.update_ability(current_question, response)
            
            # Adjust next question difficulty
            next_difficulty = algorithm.select_next_difficulty()
            session.adaptive_difficulty = next_difficulty
        
        # Move to next question
        session.current_question_index += 1
        
        # Check if quiz is completed
        if session.current_question_index >= len(session.questions):
            session.is_completed = True
            session.end_time = datetime.now()
            next_question = None
        else:
            next_question = session.get_current_question()
        
        logger.info(f"Response submitted for session {session_id}, correct: {is_correct}")
        return is_correct, next_question
    
    def complete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Complete quiz session and calculate scores.
        
        Args:
            session_id: Quiz session ID
            
        Returns:
            Dictionary with session results
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.is_completed:
            session.is_completed = True
            session.end_time = datetime.now()
        
        # Calculate scores
        results = self._calculate_session_results(session)
        
        logger.info(f"Completed quiz session {session_id} with score {results['total_score']:.1f}")
        return results
    
    def get_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a completed session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        if not session.is_completed:
            return None
        
        return self._calculate_session_results(session)
    
    def _load_question_bank(self):
        """Load question bank with sample questions."""
        # This would typically load from a database or JSON files
        # For now, we'll create sample questions
        
        # Memory questions
        memory_questions = [
            Question(
                id="mem_001",
                type=QuestionType.MULTIPLE_CHOICE,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.EASY,
                question_text="What is the capital of France?",
                options=["London", "Berlin", "Paris", "Madrid"],
                correct_answer="Paris",
                explanation="Paris is the capital and largest city of France.",
                time_limit_seconds=30
            ),
            Question(
                id="mem_002",
                type=QuestionType.PATTERN_RECOGNITION,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.MEDIUM,
                question_text="Remember this sequence: 7, 14, 21, 28. What comes next?",
                options=["35", "42", "49", "56"],
                correct_answer="35",
                explanation="The pattern adds 7 each time: 7, 14, 21, 28, 35.",
                time_limit_seconds=45
            ),
            Question(
                id="mem_003",
                type=QuestionType.MULTIPLE_CHOICE,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.EASY,
                question_text="Which planet is known as the Red Planet?",
                options=["Venus", "Mars", "Jupiter", "Saturn"],
                correct_answer="Mars",
                explanation="Mars appears red due to iron oxide on its surface.",
                time_limit_seconds=30
            ),
            Question(
                id="mem_004",
                type=QuestionType.PATTERN_RECOGNITION,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.MEDIUM,
                question_text="Complete the sequence: 2, 4, 8, 16, ___",
                options=["24", "28", "32", "64"],
                correct_answer="32",
                explanation="Each number doubles: 2×2=4, 4×2=8, 8×2=16, 16×2=32.",
                time_limit_seconds=45
            ),
            Question(
                id="mem_005",
                type=QuestionType.MULTIPLE_CHOICE,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.HARD,
                question_text="A list reads: apple, banana, cherry, date, elderberry. What was the 3rd item?",
                options=["banana", "cherry", "date", "apple"],
                correct_answer="cherry",
                explanation="The list in order: apple(1), banana(2), cherry(3), date(4), elderberry(5).",
                time_limit_seconds=20
            ),
            Question(
                id="mem_006",
                type=QuestionType.MULTIPLE_CHOICE,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.EASY,
                question_text="How many days are in a leap year?",
                options=["364", "365", "366", "367"],
                correct_answer="366",
                explanation="A leap year has 366 days, with February having 29 days.",
                time_limit_seconds=30
            ),
            Question(
                id="mem_007",
                type=QuestionType.PATTERN_RECOGNITION,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.HARD,
                question_text="Sequence: 1, 1, 2, 3, 5, 8, ___. What comes next?",
                options=["11", "12", "13", "14"],
                correct_answer="13",
                explanation="Fibonacci sequence: each number is the sum of the two preceding ones.",
                time_limit_seconds=45
            ),
            Question(
                id="mem_008",
                type=QuestionType.MULTIPLE_CHOICE,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.MEDIUM,
                question_text="What color do you get when you mix red and blue?",
                options=["Green", "Orange", "Purple", "Yellow"],
                correct_answer="Purple",
                explanation="Mixing red and blue produces purple (violet).",
                time_limit_seconds=30
            ),
            Question(
                id="mem_009",
                type=QuestionType.MULTIPLE_CHOICE,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.VERY_EASY,
                question_text="How many sides does a triangle have?",
                options=["2", "3", "4", "5"],
                correct_answer="3",
                explanation="A triangle has exactly 3 sides and 3 angles.",
                time_limit_seconds=15
            ),
            Question(
                id="mem_010",
                type=QuestionType.PATTERN_RECOGNITION,
                domain=CognitiveDomain.MEMORY,
                difficulty=DifficultyLevel.VERY_HARD,
                question_text="Sequence: 3, 6, 11, 18, 27, ___. What comes next?",
                options=["36", "38", "40", "38"],
                correct_answer="38",
                explanation="Differences: +3, +5, +7, +9, +11. Next: 27+11=38.",
                time_limit_seconds=60
            ),
        ]
        
        # Attention questions
        attention_questions = [
            Question(
                id="att_001",
                type=QuestionType.TRUE_FALSE,
                domain=CognitiveDomain.ATTENTION,
                difficulty=DifficultyLevel.EASY,
                question_text="The sky is green.",
                options=["True", "False"],
                correct_answer="False",
                explanation="The sky appears blue due to Rayleigh scattering.",
                time_limit_seconds=15
            )
        ]
        
        # Processing speed questions
        processing_questions = [
            Question(
                id="ps_001",
                type=QuestionType.NUMERICAL_REASONING,
                domain=CognitiveDomain.PROCESSING_SPEED,
                difficulty=DifficultyLevel.MEDIUM,
                question_text="What is 17 × 23?",
                options=["391", "401", "411", "421"],
                correct_answer="391",
                explanation="17 × 23 = 391",
                time_limit_seconds=30
            )
        ]
        
        # Problem solving questions
        problem_solving_questions = [
            Question(
                id="psol_001",
                type=QuestionType.LOGICAL_REASONING,
                domain=CognitiveDomain.PROBLEM_SOLVING,
                difficulty=DifficultyLevel.HARD,
                question_text="If all roses are flowers and some flowers fade quickly, which statement must be true?",
                options=[
                    "All roses fade quickly",
                    "Some roses fade quickly", 
                    "No roses fade quickly",
                    "Some flowers are roses"
                ],
                correct_answer="Some roses fade quickly",
                explanation="Since all roses are flowers and some flowers fade quickly, some roses must fade quickly.",
                time_limit_seconds=60
            )
        ]
        
        # Add to question bank
        self.question_bank[CognitiveDomain.MEMORY] = memory_questions
        self.question_bank[CognitiveDomain.ATTENTION] = attention_questions
        self.question_bank[CognitiveDomain.PROCESSING_SPEED] = processing_questions
        self.question_bank[CognitiveDomain.PROBLEM_SOLVING] = problem_solving_questions
        
        logger.info(f"Loaded question bank with {sum(len(qs) for qs in self.question_bank.values())} questions")
    
    def _select_adaptive_questions(self, domain: CognitiveDomain, num_questions: int) -> List[Question]:
        """Select questions for adaptive quiz."""
        questions = self.question_bank.get(domain, [])
        
        if not questions:
            # Create placeholder questions if none available
            return self._create_placeholder_questions(domain, num_questions)
        
        # Start with medium difficulty questions
        selected = []
        available_questions = questions.copy()
        
        # Select first question at medium difficulty
        medium_questions = [q for q in available_questions if q.difficulty == DifficultyLevel.MEDIUM]
        if medium_questions:
            selected.append(random.choice(medium_questions))
            available_questions.remove(selected[0])
        
        # Fill remaining slots (will be adapted during quiz)
        while len(selected) < num_questions and available_questions:
            selected.append(random.choice(available_questions))
            available_questions.remove(selected[-1])
        
        # Pad with shuffled copies if not enough unique questions (avoid consecutive duplicates)
        if len(selected) < num_questions:
            remaining = [q for q in questions if q not in selected]
            random.shuffle(remaining)
            pool = remaining if remaining else questions[:]
            random.shuffle(pool)
            for q in pool:
                if len(selected) >= num_questions:
                    break
                selected.append(q)
        
        return selected[:num_questions]
    
    def _select_fixed_questions(self, domain: CognitiveDomain, num_questions: int) -> List[Question]:
        """Select fixed difficulty questions."""
        questions = self.question_bank.get(domain, [])
        
        if not questions:
            return self._create_placeholder_questions(domain, num_questions)
        
        # Select questions across difficulty levels
        selected = []
        difficulties = list(DifficultyLevel)
        
        questions_per_difficulty = max(1, num_questions // len(difficulties))
        
        for difficulty in difficulties:
            difficulty_questions = [q for q in questions if q.difficulty == difficulty]
            if difficulty_questions:
                count = min(questions_per_difficulty, len(difficulty_questions))
                selected.extend(random.sample(difficulty_questions, count))
        
        # Fill remaining slots randomly
        while len(selected) < num_questions:
            selected.append(random.choice(questions))
        
        return selected[:num_questions]
    
    def _create_placeholder_questions(self, domain: CognitiveDomain, num_questions: int) -> List[Question]:
        """Create placeholder questions when question bank is empty."""
        questions = []
        
        for i in range(num_questions):
            questions.append(Question(
                id=f"placeholder_{domain.value}_{i+1:03d}",
                type=QuestionType.MULTIPLE_CHOICE,
                domain=domain,
                difficulty=DifficultyLevel.MEDIUM,
                question_text=f"Sample {domain.value} question {i+1}",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                explanation="This is a placeholder question.",
                time_limit_seconds=60
            ))
        
        return questions
    
    def _check_answer(self, question: Question, user_answer: Any) -> bool:
        """Check if user answer is correct."""
        if question.type == QuestionType.MULTIPLE_CHOICE:
            return str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
        elif question.type == QuestionType.TRUE_FALSE:
            return str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
        elif question.type == QuestionType.SHORT_ANSWER:
            return str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
        else:
            # For essay and other types, we'd need more sophisticated checking
            return str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
    
    def _calculate_session_results(self, session: QuizSession) -> Dict[str, Any]:
        """Calculate comprehensive session results."""
        if not session.responses:
            return {
                "session_id": session.id,
                "total_score": 0.0,
                "percentage": 0.0,
                "correct_answers": 0,
                "total_questions": len(session.questions),
                "time_spent_seconds": session.get_time_spent(),
                "domain_scores": {},
                "difficulty_performance": {},
                "response_times": [],
                "recommendations": []
            }
        
        # Basic metrics
        correct_count = sum(1 for r in session.responses if r.is_correct)
        total_questions = len(session.questions)
        total_possible = sum(q.points_possible for q in session.questions)
        total_score = sum(q.points_possible for i, q in enumerate(session.questions) if session.responses[i].is_correct)
        percentage = (total_score / total_possible) * 100 if total_possible > 0 else 0
        
        # Response times
        response_times = [r.response_time_ms for r in session.responses]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Domain scores (all questions are in the same domain for now)
        domain_scores = {
            session.domain.value: {
                "score": percentage,
                "correct": correct_count,
                "total": total_questions,
                "avg_response_time_ms": avg_response_time
            }
        }
        
        # Difficulty performance
        difficulty_performance = {}
        for i, response in enumerate(session.responses):
            if i < len(session.questions):
                question = session.questions[i]
                difficulty = question.difficulty.value
                if difficulty not in difficulty_performance:
                    difficulty_performance[difficulty] = {"correct": 0, "total": 0}
                difficulty_performance[difficulty]["total"] += 1
                if response.is_correct:
                    difficulty_performance[difficulty]["correct"] += 1
        
        # Calculate percentages for each difficulty
        for difficulty in difficulty_performance:
            perf = difficulty_performance[difficulty]
            perf["percentage"] = (perf["correct"] / perf["total"]) * 100 if perf["total"] > 0 else 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(session, percentage, difficulty_performance)
        
        # Adaptive algorithm results
        adaptive_results = {}
        if session.id in self.adaptive_algorithms:
            algorithm = self.adaptive_algorithms[session.id]
            adaptive_results = {
                "final_ability_estimate": algorithm.ability_estimate,
                "ability_uncertainty": algorithm.ability_std,
                "difficulty_progression": [q.difficulty.value for q in session.questions]
            }
        
        return {
            "session_id": session.id,
            "quiz_type": session.quiz_type,
            "domain": session.domain.value,
            "total_score": total_score,
            "percentage": percentage,
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "time_spent_seconds": session.get_time_spent(),
            "avg_response_time_ms": avg_response_time,
            "domain_scores": domain_scores,
            "difficulty_performance": difficulty_performance,
            "adaptive_results": adaptive_results,
            "recommendations": recommendations,
            "completed_at": session.end_time.isoformat() if session.end_time else None
        }
    
    def _generate_recommendations(
        self, 
        session: QuizSession, 
        percentage: float, 
        difficulty_performance: Dict[str, Dict]
    ) -> List[str]:
        """Generate personalized recommendations based on performance."""
        recommendations = []
        
        # Overall performance recommendations
        if percentage >= 90:
            recommendations.append("Excellent performance! Consider advanced exercises in this domain.")
        elif percentage >= 70:
            recommendations.append("Good performance! Focus on challenging yourself with harder problems.")
        elif percentage >= 50:
            recommendations.append("Fair performance. Practice with medium-difficulty exercises to improve.")
        else:
            recommendations.append("Consider foundational exercises in this domain to build confidence.")
        
        # Difficulty-specific recommendations
        for difficulty, perf in difficulty_performance.items():
            if perf["percentage"] < 50 and perf["total"] >= 3:
                recommendations.append(f"Focus on {difficulty} difficulty questions to improve accuracy.")
        
        # Response time recommendations
        avg_time = sum(r.response_time_ms for r in session.responses) / len(session.responses) if session.responses else 0
        if avg_time > 45000:  # 45 seconds
            recommendations.append("Try to improve your response time while maintaining accuracy.")
        
        return recommendations
