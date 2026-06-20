---
description: Development story workflow for technical implementation details
---

# Dev Story - Technical Implementation Workflow

## Purpose
Create detailed technical development stories with implementation specifics, technical requirements, and code-level details for the development team.

## Dev Story Format

```
Technical Story: [Title]
Module: [Component/Module]
Developer: [Assigned Developer]
Estimated Time: [Hours/Days]

Technical Requirements:
- [Requirement 1]
- [Requirement 2]

Implementation Details:
- [Technical approach 1]
- [Technical approach 2]

Acceptance Criteria:
- Given [technical context]
- When [technical action]
- Then [technical outcome]

Testing Strategy:
- Unit tests: [coverage requirements]
- Integration tests: [scenarios]
- Performance tests: [metrics]

Dependencies:
- [External dependencies]
- [Internal dependencies]

Risks & Mitigations:
- [Risk 1]: [Mitigation]
```

## Generated Development Stories

### **Story 1: Repository Setup (Frontend, Backend, ML)**

```
Technical Story: Multi-Repository Setup with Standard Structure
Module: Infrastructure Foundation
Developer: Full Stack DevOps Engineer
Estimated Time: 2 days

Technical Requirements:
- Create 3 separate repositories: kash-frontend, kash-backend, kash-ml
- Implement monorepo structure with shared configurations
- Setup TypeScript, ESLint, Prettier across all repos
- Configure package.json with proper dependencies
- Implement Git branching strategy (main, develop, feature/*)

Implementation Details:
Frontend Repository (kash-frontend):
- React 18 with TypeScript
- TailwindCSS for styling
- Recharts for data visualization
- React Router for navigation
- Axios for API communication
- Vite for build tooling

Backend Repository (kash-backend):
- Node.js 18+ with TypeScript
- Express.js framework
- PostgreSQL client (pg)
- JWT authentication
- API documentation with Swagger
- Winston for logging

ML Repository (kash-ml):
- Python 3.9+ environment
- FastAPI for ML model serving
- Scikit-learn, TensorFlow, PyTorch
- Pandas, NumPy for data processing
- MLflow for model tracking
- SHAP for explainability

Acceptance Criteria:
- Given repository creation requirements
- When all repositories are initialized
- Then each repo has proper structure, dependencies, and can run locally

Testing Strategy:
- Unit tests: Jest for frontend/backend, pytest for ML
- Integration tests: API endpoint testing
- Performance tests: Build time <2min, test suite <5min

Dependencies:
- GitHub/GitLab for repository hosting
- Node.js 18+, Python 3.9+
- Package managers: npm/yarn, pip/conda

Risks & Mitigations:
- Repository sync issues: Use shared configuration files
- Dependency conflicts: Version locking in package.json
```

### **Story 2: CI/CD Pipeline Configuration**

```
Technical Story: GitHub Actions CI/CD with Automated Testing and Deployment
Module: DevOps Pipeline
Developer: DevOps Engineer
Estimated Time: 3 days

Technical Requirements:
- Configure GitHub Actions workflows for all 3 repositories
- Implement automated testing on each push/PR
- Setup automated security scanning
- Configure deployment to staging/production environments
- Implement rollback mechanisms

Implementation Details:
CI Pipeline (.github/workflows/ci.yml):
- Trigger on push to main/develop and pull requests
- Linting with ESLint, Prettier, Black (Python)
- Unit test execution with coverage reporting
- Security scanning with CodeQL, Dependabot
- Build artifacts creation and storage

CD Pipeline (.github/workflows/deploy.yml):
- Environment-specific deployments (staging/prod)
- Database migrations execution
- Health checks and smoke tests
- Rollback automation on failure
- Slack/Teams notifications

Quality Gates:
- Test coverage >80%
- No critical security vulnerabilities
- Build success rate >95%
- Performance benchmarks met

Acceptance Criteria:
- Given code changes pushed to repository
- When CI/CD pipeline executes
- Then tests pass, security scans complete, and deployment succeeds

Testing Strategy:
- Pipeline testing: Mock deployments to test environment
- Integration testing: End-to-end pipeline validation
- Performance testing: Pipeline execution time <10min

Dependencies:
- GitHub Actions for workflow orchestration
- AWS/GCP/Azure for deployment targets
- Docker for containerization
- Kubernetes for orchestration (optional)

Risks & Mitigations:
- Pipeline failures: Implement comprehensive error handling
- Deployment conflicts: Use blue-green deployment strategy
- Security breaches: Regular security audits and updates
```

### **Story 3: Cloud Infrastructure Deployment**

```
Technical Story: Multi-Cloud Infrastructure Setup with High Availability
Module: Cloud Infrastructure
Developer: Cloud Architect
Estimated Time: 3 days

Technical Requirements:
- Deploy infrastructure on AWS/GCP/Azure
- Configure staging and production environments
- Implement high availability and auto-scaling
- Setup networking, security, and monitoring
- Configure backup and disaster recovery

Implementation Details:
Infrastructure Components:
- Compute: EC2 instances or Cloud Run
- Database: RDS PostgreSQL with read replicas
- Storage: S3/GCS for file storage
- Networking: VPC with subnets and security groups
- Load Balancing: Application Load Balancer
- Caching: Redis/ElastiCache

Security Configuration:
- IAM roles and policies
- Security groups and NACLs
- SSL/TLS certificates
- WAF for DDoS protection
- Encryption at rest and in transit

Monitoring & Logging:
- CloudWatch/GCP Monitoring
- Application performance monitoring
- Error tracking and alerting
- Log aggregation and analysis

Acceptance Criteria:
- Given infrastructure requirements
- When deployment scripts execute
- Then all environments are configured with proper security and monitoring

Testing Strategy:
- Infrastructure testing: Terraform validation
- Load testing: Simulate traffic patterns
- Security testing: Penetration testing
- Disaster recovery: Backup/restore testing

Dependencies:
- Terraform/CloudFormation for IaC
- Docker for containerization
- Kubernetes for orchestration
- Monitoring tools (Datadog/New Relic)

Risks & Mitigations:
- Cloud provider outages: Multi-cloud strategy
- Cost overruns: Budget alerts and optimization
- Security breaches: Regular security audits
- Performance issues: Auto-scaling and monitoring
```

### **Story 4: Database Schema Setup**

```
Technical Story: PostgreSQL Database Schema with KASH Data Model
Module: Database Layer
Developer: Backend/Database Engineer
Estimated Time: 2 days

Technical Requirements:
- Design PostgreSQL schema for KASH platform
- Implement database migrations with versioning
- Setup indexes for performance optimization
- Configure foreign keys and constraints
- Implement backup and restore procedures

Implementation Details:
Core Tables:
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    institution_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- KASH profiles table
CREATE TABLE kash_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    knowledge_score FLOAT,
    abilities_score FLOAT,
    skills_score FLOAT,
    habits_score FLOAT,
    overall_kash_score FLOAT,
    weights JSONB,
    evaluation_date TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    required_knowledge FLOAT,
    required_abilities FLOAT,
    required_skills FLOAT,
    required_habits FLOAT,
    esco_code VARCHAR(50),
    onet_code VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Compatibility scores table
CREATE TABLE compatibility_scores (
    user_id UUID REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    compatibility_score FLOAT,
    success_probability FLOAT,
    explanation JSONB,
    calculated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, job_id)
);
```

Indexes and Performance:
- B-tree indexes on foreign keys
- GIN indexes on JSONB columns
- Partial indexes for common queries
- Composite indexes for complex queries

Migration Strategy:
- Use database migration tool (Flyway/Liquibase)
- Version-controlled schema changes
- Rollback capabilities for each migration
- Test migrations on staging first

Acceptance Criteria:
- Given database migration scripts
- When migrations are executed
- Then all tables are created with proper relationships and indexes

Testing Strategy:
- Unit tests: Schema validation
- Integration tests: Data integrity checks
- Performance tests: Query optimization
- Load testing: Concurrent access patterns

Dependencies:
- PostgreSQL 14+ database
- Migration tool (Flyway/Liquibase)
- Database connection pool (PgBouncer)
- Backup tool (pg_dump/WAL-E)

Risks & Mitigations:
- Data corruption: Regular backups and validation
- Performance issues: Query optimization and indexing
- Schema changes: Careful migration planning
- Data loss: Comprehensive backup strategy
```

### **Story 5: Development Environment Templates**

```
Technical Story: Docker-Based Development Environment with Team Consistency
Module: Development Environment
Developer: Full Stack Engineer
Estimated Time: 2 days

Technical Requirements:
- Create Docker development containers for all services
- Setup docker-compose for local development
- Implement hot-reload and debugging capabilities
- Configure environment variables and secrets management
- Create onboarding documentation

Implementation Details:
Docker Compose Setup (docker-compose.dev.yml):
```yaml
version: '3.8'
services:
  frontend:
    build: ./kash-frontend
    ports:
      - "3000:3000"
    volumes:
      - ./kash-frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    command: npm start

  backend:
    build: ./kash-backend
    ports:
      - "8000:8000"
    volumes:
      - ./kash-backend:/app
      - /app/node_modules
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/kash_dev
      - JWT_SECRET=dev_secret
    depends_on:
      - postgres
    command: npm run dev

  ml-service:
    build: ./kash-ml
    ports:
      - "8001:8000"
    volumes:
      - ./kash-ml:/app
    environment:
      - MODEL_PATH=/app/models
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  postgres:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=kash_dev
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

Development Dockerfiles:
- Multi-stage builds for optimization
- Development-specific configurations
- Hot-reload capabilities
- Debug tools and profilers

Environment Management:
- .env files for local development
- Environment variable validation
- Secret management with Doppler/AWS Secrets Manager
- Configuration validation at startup

Acceptance Criteria:
- Given a new developer joining the team
- When they run docker-compose up
- Then all services start correctly with hot-reload enabled

Testing Strategy:
- Container testing: Validate Docker builds
- Integration testing: Service communication
- Performance testing: Startup time <30s
- Onboarding testing: New developer setup

Dependencies:
- Docker and Docker Compose
- Node.js 18+, Python 3.9+
- PostgreSQL 14+
- Redis for caching

Risks & Mitigations:
- Container conflicts: Proper port mapping
- Performance issues: Resource limits and optimization
- Environment drift: Standardized configurations
- Setup complexity: Comprehensive documentation
```

## Development Story Summary

| Story | Module | Developer | Time | Dependencies |
|-------|--------|-----------|------|-------------|
| Repository Setup | Infrastructure | Full Stack DevOps | 2 days | Git provider, Node.js, Python |
| CI/CD Pipeline | DevOps | DevOps Engineer | 3 days | GitHub Actions, Cloud provider |
| Cloud Infrastructure | Cloud | Cloud Architect | 3 days | Terraform, AWS/GCP/Azure |
| Database Schema | Database | Backend Engineer | 2 days | PostgreSQL, Migration tool |
| Dev Environment | Development | Full Stack | 2 days | Docker, Docker Compose |

**Total Estimated Time: 12 days**

### **Story 6: NLP CV Analysis Engine**

```
Technical Story: Natural Language Processing CV Analysis with Knowledge Extraction
Module: Knowledge Evaluation - NLP Engine
Developer: ML/NLP Engineer
Estimated Time: 3 days

Technical Requirements:
- Implement NLP pipeline for CV text processing
- Extract knowledge domains, skills, and experience levels
- Integrate with ESCO/O*NET classification system
- Support multiple CV formats (PDF, DOCX, TXT)
- Implement confidence scoring for extracted information

Implementation Details:
NLP Pipeline Architecture:
```python
# Core NLP processing pipeline
class CVAnalysisEngine:
    def __init__(self):
        self.nlp_model = spacy.load("en_core_web_lg")
        self.skill_extractor = SkillExtractor()
        self.knowledge_classifier = KnowledgeClassifier()
    
    def analyze_cv(self, cv_text: str) -> CVAnalysis:
        # Text preprocessing
        cleaned_text = self.preprocess_text(cv_text)
        
        # Named entity recognition
        doc = self.nlp_model(cleaned_text)
        
        # Extract skills and knowledge
        skills = self.skill_extractor.extract(doc)
        knowledge_domains = self.knowledge_classifier.classify(doc)
        
        # Experience level analysis
        experience = self.analyze_experience(doc)
        
        return CVAnalysis(
            skills=skills,
            knowledge_domains=knowledge_domains,
            experience_level=experience,
            confidence_scores=self.calculate_confidence()
        )
```

Knowledge Extraction Algorithms:
- **Named Entity Recognition**: Custom NER model for skills/qualifications
- **Text Classification**: BERT-based knowledge domain classification
- **Experience Analysis**: Rule-based + ML for seniority detection
- **Skill Validation**: Cross-reference with ESCO skill database

File Processing:
- PDF parsing with PyPDF2/pdfplumber
- DOCX processing with python-docx
- OCR integration for scanned documents (Tesseract)
- Text cleaning and normalization

Acceptance Criteria:
- Given a CV file uploaded
- When the NLP analysis runs
- Then knowledge domains, skills, and experience are extracted with >80% accuracy

Testing Strategy:
- Unit tests: Individual NLP components
- Integration tests: End-to-end CV processing
- Performance tests: Processing time <30s per CV
- Accuracy tests: Manual validation against ground truth

Dependencies:
- spaCy for NLP processing
- Transformers library for BERT models
- ESCO API for skill validation
- PDF/DOCX parsing libraries

Risks & Mitigations:
- Low accuracy on complex CVs: Ensemble of models + manual review
- File format issues: Comprehensive error handling
- Performance bottlenecks: Async processing + caching
- Language limitations: Multi-language model support
```

### **Story 7: ESCO/O*NET Integration**

```
Technical Story: European Skills/Competences/Occupations and O*NET Data Integration
Module: Knowledge Mapping - External APIs
Developer: Backend Integration Engineer
Estimated Time: 2 days

Technical Requirements:
- Integrate ESCO API for European job classification
- Integrate O*NET API for US job market data
- Implement caching strategy for API responses
- Create local database of job classifications
- Handle API rate limits and fallback mechanisms

Implementation Details:
API Integration Architecture:
```python
class JobClassificationService:
    def __init__(self):
        self.esco_client = ESCOClient()
        self.onet_client = ONETClient()
        self.redis_client = Redis()
        self.cache_ttl = 86400  # 24 hours
    
    async def get_job_classification(self, skill_keywords: List[str]) -> JobClassification:
        cache_key = f"job_classification:{hash(skill_keywords)}"
        
        # Check cache first
        cached_result = await self.redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Parallel API calls
        esco_results = await self.esco_client.search_skills(skill_keywords)
        onet_results = await self.onet_client.search_occupations(skill_keywords)
        
        # Merge and rank results
        merged_results = self.merge_classifications(esco_results, onet_results)
        
        # Cache results
        await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(merged_results))
        
        return merged_results
```

Data Models:
```sql
-- ESCO classifications
CREATE TABLE esco_classifications (
    id UUID PRIMARY KEY,
    concept_uri VARCHAR(255) UNIQUE,
    preferred_label VARCHAR(255),
    description TEXT,
    skill_type VARCHAR(50),
    relevance_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- O*NET classifications
CREATE TABLE onet_classifications (
    id UUID PRIMARY KEY,
    code VARCHAR(10) UNIQUE,
    title VARCHAR(255),
    description TEXT,
    tasks_required TEXT[],
    knowledge_required JSONB,
    skills_required JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Rate Limiting Strategy:
- ESCO API: 1000 requests/hour with exponential backoff
- O*NET API: 1000 requests/day with request queuing
- Redis caching with 24-hour TTL
- Fallback to local database when APIs unavailable

Acceptance Criteria:
- Given skill keywords from CV analysis
- When the classification service runs
- Then relevant job classifications are returned with confidence scores

Testing Strategy:
- Unit tests: API client implementations
- Integration tests: End-to-end classification flow
- Performance tests: API response time <2s
- Load tests: Handle 100 concurrent requests

Dependencies:
- ESCO API client
- O*NET API client
- Redis for caching
- Async HTTP client (aiohttp)

Risks & Mitigations:
- API rate limits: Comprehensive caching and queuing
- API downtime: Local database fallback
- Data inconsistency: Regular data synchronization
- Performance issues: Async processing and caching
```

### **Story 8: Adaptive Quiz Algorithm**

```
Technical Story: Adaptive Testing Algorithm with Dynamic Difficulty Adjustment
Module: Knowledge Evaluation - Quiz Engine
Developer: Backend/ML Engineer
Estimated Time: 3 days

Technical Requirements:
- Implement Item Response Theory (IRT) for adaptive testing
- Create dynamic difficulty adjustment algorithm
- Support multiple question types (multiple choice, text, practical)
- Implement knowledge gap identification
- Provide real-time feedback and scoring

Implementation Details:
Adaptive Testing Algorithm:
```python
class AdaptiveQuizEngine:
    def __init__(self):
        self.irt_model = IRTModel()
        self.question_bank = QuestionBank()
        self.difficulty_estimator = DifficultyEstimator()
    
    def select_next_question(self, user_responses: List[QuizResponse]) -> Question:
        # Estimate current ability level
        current_ability = self.irt_model.estimate_ability(user_responses)
        
        # Select optimal question difficulty
        target_difficulty = current_ability
        
        # Filter unanswered questions
        available_questions = self.question_bank.get_unanswered(user_responses)
        
        # Select question with closest difficulty
        next_question = self.difficulty_estimator.select_optimal(
            available_questions, 
            target_difficulty
        )
        
        return next_question
    
    def update_ability_estimate(self, response: QuizResponse) -> float:
        # Update IRT parameters
        self.irt_model.update_parameters(response)
        
        # Return new ability estimate
        return self.irt_model.estimate_ability(response.user_responses)
```

Question Difficulty Models:
- **3-Parameter IRT Model**: Discrimination, difficulty, guessing parameters
- **Bayesian updating**: Continuous ability estimation
- **Knowledge domain tracking**: Separate ability per domain
- **Confidence intervals**: Statistical uncertainty quantification

Question Bank Structure:
```sql
CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY,
    knowledge_domain VARCHAR(100),
    question_type VARCHAR(50),
    difficulty FLOAT,
    discrimination FLOAT,
    guessing FLOAT,
    content TEXT,
    options JSONB,
    correct_answer VARCHAR(255),
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_quiz_responses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    question_id UUID REFERENCES quiz_questions(id),
    selected_answer VARCHAR(255),
    response_time INTEGER,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given a quiz session in progress
- When a user answers questions
- Then question difficulty adapts based on performance and knowledge gaps are identified

Testing Strategy:
- Unit tests: IRT algorithm accuracy
- Integration tests: Complete quiz flow
- Performance tests: Question selection <100ms
- Accuracy tests: Ability estimation error <0.1

Dependencies:
- NumPy/SciPy for mathematical computations
- Psychometric libraries for IRT implementation
- PostgreSQL for question storage
- Redis for session management

Risks & Mitigations:
- Algorithm complexity: Thorough testing and validation
- Performance issues: Efficient algorithms and caching
- Question bank quality: Expert review and validation
- User frustration: Progress indicators and help system
```

### **Story 9: Knowledge Scoring Calculation**

```
Technical Story: Multi-Source Knowledge Score Aggregation with Weighted Formula
Module: Knowledge Evaluation - Scoring Engine
Developer: Backend/ML Engineer
Estimated Time: 2 days

Technical Requirements:
- Implement weighted scoring algorithm for knowledge evaluation
- Aggregate scores from CV analysis, quiz results, and ESCO mapping
- Calculate confidence intervals for each score component
- Support dynamic weight adjustment based on data quality
- Provide detailed score breakdown and explanations

Implementation Details:
Scoring Algorithm:
```python
class KnowledgeScoringEngine:
    def __init__(self):
        self.weights = {
            'cv_analysis': 0.3,
            'quiz_results': 0.4,
            'esco_mapping': 0.3
        }
        self.confidence_calculator = ConfidenceCalculator()
    
    def calculate_knowledge_score(self, user_id: UUID) -> KnowledgeScore:
        # Get individual component scores
        cv_score = self.get_cv_analysis_score(user_id)
        quiz_score = self.get_quiz_results_score(user_id)
        esco_score = self.get_esco_mapping_score(user_id)
        
        # Calculate component confidences
        cv_confidence = self.confidence_calculator.calculate(cv_score)
        quiz_confidence = self.confidence_calculator.calculate(quiz_score)
        esco_confidence = self.confidence_calculator.calculate(esco_score)
        
        # Dynamic weight adjustment based on confidence
        adjusted_weights = self.adjust_weights_by_confidence(
            self.weights,
            [cv_confidence, quiz_confidence, esco_confidence]
        )
        
        # Calculate weighted score
        overall_score = (
            adjusted_weights['cv_analysis'] * cv_score.score +
            adjusted_weights['quiz_results'] * quiz_score.score +
            adjusted_weights['esco_mapping'] * esco_score.score
        )
        
        # Calculate overall confidence
        overall_confidence = self.calculate_overall_confidence(
            [cv_confidence, quiz_confidence, esco_confidence],
            adjusted_weights
        )
        
        return KnowledgeScore(
            overall_score=overall_score,
            confidence_interval=overall_confidence,
            component_scores={
                'cv_analysis': cv_score,
                'quiz_results': quiz_score,
                'esco_mapping': esco_score
            },
            weights_used=adjusted_weights
        )
```

Score Components:
- **CV Analysis Score**: NLP confidence + skill relevance
- **Quiz Results Score**: IRT ability estimate + response consistency
- **ESCO Mapping Score**: Classification confidence + domain coverage

Confidence Calculation:
- **Statistical confidence**: Standard error, confidence intervals
- **Data quality confidence**: Completeness, recency, source reliability
- **Model confidence**: Prediction probability, ensemble agreement

Acceptance Criteria:
- Given completed knowledge evaluations
- When the scoring engine runs
- Then a comprehensive knowledge score is calculated with confidence intervals

Testing Strategy:
- Unit tests: Individual scoring components
- Integration tests: Complete scoring pipeline
- Accuracy tests: Score validation against expert ratings
- Performance tests: Calculation time <500ms

Dependencies:
- NumPy/SciPy for mathematical computations
- PostgreSQL for score storage
- Redis for caching intermediate results
- Statistical libraries for confidence calculations

Risks & Mitigations:
- Score inconsistency: Regular calibration and validation
- Weight bias: Dynamic adjustment and transparency
- Performance issues: Efficient algorithms and caching
- User confusion: Detailed explanations and visualizations
```

### **Story 10: Frontend Evaluation Interface**

```
Technical Story: Interactive Knowledge Evaluation Interface with Real-time Feedback
Module: Frontend - Knowledge Module
Developer: Frontend Engineer
Estimated Time: 2 days

Technical Requirements:
- Create responsive interface for knowledge evaluation
- Implement CV upload and analysis visualization
- Build interactive quiz interface with adaptive questions
- Display comprehensive results dashboard
- Support progress tracking and session management

Implementation Details:
React Components Structure:
```typescript
// Main evaluation container
const KnowledgeEvaluation: React.FC = () => {
  const [evaluationState, setEvaluationState] = useState<EvaluationState>('initial');
  const [userProgress, setUserProgress] = useState<UserProgress>({});
  const [results, setResults] = useState<KnowledgeResults | null>(null);

  return (
    <div className="knowledge-evaluation">
      <EvaluationHeader state={evaluationState} />
      <EvaluationProgress progress={userProgress} />
      
      {evaluationState === 'cv-upload' && (
        <CVUploadSection onUpload={handleCVUpload} />
      )}
      
      {evaluationState === 'quiz' && (
        <QuizInterface onAnswer={handleQuizAnswer} />
      )}
      
      {evaluationState === 'results' && (
        <ResultsDashboard results={results} />
      )}
    </div>
  );
};

// CV upload component
const CVUploadSection: React.FC<{onUpload: (file: File) => void}> = ({ onUpload }) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisResults, setAnalysisResults] = useState<CVAnalysis | null>(null);

  return (
    <div className="cv-upload-section">
      <FileUploader
        accept=".pdf,.docx,.txt"
        onUpload={onUpload}
        onProgress={setUploadProgress}
      />
      
      {analysisResults && (
        <CVAnalysisResults results={analysisResults} />
      )}
    </div>
  );
};

// Quiz interface component
const QuizInterface: React.FC<{onAnswer: (answer: string) => void}> = ({ onAnswer }) => {
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(300); // 5 minutes

  return (
    <div className="quiz-interface">
      <QuizTimer timeRemaining={timeRemaining} />
      <QuestionDisplay question={currentQuestion} />
      <AnswerOptions onAnswer={onAnswer} />
      <QuizProgress current={currentQuestion?.number} total={totalQuestions} />
    </div>
  );
};
```

State Management:
- **Redux Toolkit**: Global evaluation state
- **React Query**: API data fetching and caching
- **Local Storage**: Session persistence
- **WebSocket**: Real-time updates for adaptive questions

Data Visualization:
- **Recharts**: Score radar charts and progress graphs
- **D3.js**: Advanced knowledge domain visualizations
- **Custom components**: Interactive skill maps
- **Animations**: Smooth transitions between evaluation steps

Acceptance Criteria:
- Given access to the knowledge evaluation module
- When a user completes the evaluation process
- Then they experience a smooth, intuitive interface with real-time feedback

Testing Strategy:
- Unit tests: Component behavior and state management
- Integration tests: API integration and data flow
- E2E tests: Complete evaluation journey
- Performance tests: Page load <2s, interactions <100ms

Dependencies:
- React 18 with TypeScript
- TailwindCSS for styling
- Recharts for data visualization
- React Query for API management
- Redux Toolkit for state management

Risks & Mitigations:
- User experience issues: Usability testing and iteration
- Performance bottlenecks: Code splitting and lazy loading
- State management complexity: Clear architecture and documentation
- Mobile responsiveness: Responsive design and testing
```

## Development Story Summary

| Story | Module | Developer | Time | Dependencies |
|-------|--------|-----------|------|-------------|
| Repository Setup | Infrastructure | Full Stack DevOps | 2 days | Git provider, Node.js, Python |
| CI/CD Pipeline | DevOps | DevOps Engineer | 3 days | GitHub Actions, Cloud provider |
| Cloud Infrastructure | Cloud | Cloud Architect | 3 days | Terraform, AWS/GCP/Azure |
| Database Schema | Database | Backend Engineer | 2 days | PostgreSQL, Migration tool |
| Dev Environment | Development | Full Stack | 2 days | Docker, Docker Compose |
| NLP CV Analysis | Knowledge - NLP | ML/NLP Engineer | 3 days | spaCy, Transformers, ESCO |
| ESCO Integration | Knowledge - API | Backend Integration | 2 days | ESCO/O*NET APIs, Redis |
| Adaptive Quiz | Knowledge - Quiz | Backend/ML Engineer | 3 days | IRT models, PostgreSQL |
| Knowledge Scoring | Knowledge - Scoring | Backend/ML Engineer | 2 days | NumPy, PostgreSQL |
| Frontend Interface | Knowledge - UI | Frontend Engineer | 2 days | React, Recharts, Redux |

**Total Estimated Time: 24 days (Sprint 0-1)**

### **Story 11: Text-Based Cognitive Tests**

```
Technical Story: Text-Based Cognitive Assessment Engine for Abilities Evaluation
Module: Abilities Evaluation - Text Tests
Developer: Backend/ML Engineer
Estimated Time: 3 days

Technical Requirements:
- Implement text-based cognitive tests for logical reasoning
- Create analytical scenarios and problem-solving tasks
- Support multiple question formats (multiple choice, text input, essay)
- Implement real-time scoring and feedback
- Track response time and confidence levels

Implementation Details:
Cognitive Test Framework:
```python
class CognitiveTestEngine:
    def __init__(self):
        self.test_generator = TestGenerator()
        self.scoring_engine = CognitiveScoringEngine()
        self.time_tracker = ResponseTimeTracker()
        self.confidence_estimator = ConfidenceEstimator()
    
    def generate_test_session(self, test_type: str, difficulty: float) -> TestSession:
        questions = self.test_generator.generate_questions(
            test_type=test_type,
            difficulty=difficulty,
            question_count=10
        )
        
        return TestSession(
            id=uuid.uuid4(),
            test_type=test_type,
            questions=questions,
            start_time=datetime.now(),
            time_limit=1800  # 30 minutes
        )
    
    def evaluate_response(self, response: TestResponse) -> CognitiveScore:
        # Calculate accuracy score
        accuracy = self.scoring_engine.calculate_accuracy(response)
        
        # Analyze response time
        time_analysis = self.time_tracker.analyze(response.response_time)
        
        # Estimate confidence
        confidence = self.confidence_estimator.estimate(response)
        
        # Calculate overall cognitive score
        overall_score = self.calculate_cognitive_score(
            accuracy, time_analysis, confidence
        )
        
        return CognitiveScore(
            accuracy=accuracy,
            time_efficiency=time_analysis.efficiency,
            confidence=confidence,
            overall_score=overall_score,
            reasoning_breakdown=self.analyze_reasoning(response)
        )
```

Test Types Implementation:
- **Logical Reasoning**: Syllogisms, pattern recognition, deductive reasoning
- **Analytical Thinking**: Data interpretation, critical analysis, problem decomposition
- **Verbal Reasoning**: Text comprehension, vocabulary, analogies
- **Numerical Reasoning**: Mathematical problems, data analysis, quantitative reasoning

Question Generation Algorithm:
```python
class TestGenerator:
    def generate_logical_reasoning_question(self, difficulty: float) -> Question:
        # Generate premises and conclusion
        premises = self.generate_premises(difficulty)
        conclusion = self.generate_conclusion(premises)
        
        # Create multiple choice options
        options = self.generate_options(premises, conclusion)
        
        return Question(
            type="logical_reasoning",
            difficulty=difficulty,
            premises=premises,
            conclusion=conclusion,
            options=options,
            correct_answer=self.determine_correct_answer(premises, conclusion)
        )
    
    def generate_analytical_scenario(self, difficulty: float) -> Question:
        # Create complex scenario
        scenario = self.create_scenario(difficulty)
        
        # Generate analysis questions
        questions = self.create_analysis_questions(scenario)
        
        return Question(
            type="analytical_scenario",
            difficulty=difficulty,
            scenario=scenario,
            questions=questions,
            evaluation_criteria=self.define_criteria(difficulty)
        )
```

Database Schema:
```sql
CREATE TABLE cognitive_tests (
    id UUID PRIMARY KEY,
    test_type VARCHAR(50),
    difficulty FLOAT,
    question_data JSONB,
    scoring_criteria JSONB,
    time_limit INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_cognitive_responses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    test_id UUID REFERENCES cognitive_tests(id),
    response_data JSONB,
    response_time INTEGER,
    confidence FLOAT,
    score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given access to cognitive tests
- When a user completes text-based assessments
- Then their reasoning abilities are evaluated with detailed scoring breakdown

Testing Strategy:
- Unit tests: Individual test generation and scoring
- Integration tests: Complete test session flow
- Performance tests: Question generation <200ms, scoring <100ms
- Accuracy tests: Score validation against expert evaluations

Dependencies:
- NumPy/SciPy for mathematical computations
- NLTK/spaCy for text processing
- PostgreSQL for test storage
- Redis for session management

Risks & Mitigations:
- Question quality: Expert review and validation
- Cheating prevention: Randomization and time tracking
- Performance issues: Efficient algorithms and caching
- Cultural bias: Diverse question pools and validation
```

### **Story 12: Voice Recording Interface**

```
Technical Story: Voice Recording Interface for Abilities Evaluation
Module: Abilities Evaluation - Voice Interface
Developer: Frontend Engineer
Estimated Time: 2 days

Technical Requirements:
- Create web-based voice recording interface
- Support multiple audio formats and quality settings
- Implement real-time audio visualization and feedback
- Handle recording permissions and device management
- Provide audio preview and re-recording capabilities

Implementation Details:
React Voice Recording Component:
```typescript
interface VoiceRecorderProps {
  onRecordingComplete: (audioBlob: Blob, metadata: AudioMetadata) => void;
  maxDuration: number; // seconds
  audioQuality: 'low' | 'medium' | 'high';
  questionPrompt: string;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onRecordingComplete,
  maxDuration = 300,
  audioQuality = 'medium',
  questionPrompt
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: audioQuality === 'high' ? 48000 : 44100
        }
      });
      
      // Setup audio context for visualization
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      // Setup media recorder
      const mimeType = getSupportedMimeType();
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      
      const chunks: BlobPart[] = [];
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunks, { type: mimeType });
        setAudioBlob(blob);
        onRecordingComplete(blob, {
          duration: recordingTime,
          sampleRate: audioContextRef.current?.sampleRate || 44100,
          format: mimeType,
          quality: audioQuality
        });
      };
      
      mediaRecorderRef.current.start(100); // Collect data every 100ms
      setIsRecording(true);
      startTimer();
      startAudioVisualization();
      
    } catch (error) {
      console.error('Error starting recording:', error);
      // Handle permission denied or other errors
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      stopTimer();
      stopAudioVisualization();
    }
  };

  const startTimer = () => {
    timerRef.current = setInterval(() => {
      setRecordingTime(prev => {
        if (prev >= maxDuration) {
          stopRecording();
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
  };

  const startAudioVisualization = () => {
    const updateAudioLevel = () => {
      if (analyserRef.current && isRecording) {
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average / 255);
        requestAnimationFrame(updateAudioLevel);
      }
    };
    updateAudioLevel();
  };

  return (
    <div className="voice-recorder">
      <div className="question-prompt">
        <h3>{questionPrompt}</h3>
      </div>
      
      <div className="recording-controls">
        {!isRecording ? (
          <button onClick={startRecording} className="record-button">
            <MicIcon />
            Start Recording
          </button>
        ) : (
          <button onClick={stopRecording} className="stop-button">
            <StopIcon />
            Stop Recording
          </button>
        )}
        
        {isRecording && (
          <button onClick={() => setIsPaused(!isPaused)} className="pause-button">
            {isPaused ? <PlayIcon /> : <PauseIcon />}
          </button>
        )}
      </div>
      
      <div className="recording-info">
        <div className="timer">
          {formatTime(recordingTime)} / {formatTime(maxDuration)}
        </div>
        
        <div className="audio-visualizer">
          <AudioVisualizer audioLevel={audioLevel} isActive={isRecording} />
        </div>
      </div>
      
      {audioBlob && (
        <div className="audio-preview">
          <AudioPlayer audioBlob={audioBlob} />
          <button onClick={() => setAudioBlob(null)} className="re-record">
            Re-record
          </button>
        </div>
      )}
    </div>
  );
};
```

Audio Visualization Component:
```typescript
const AudioVisualizer: React.FC<{audioLevel: number; isActive: boolean}> = ({ 
  audioLevel, 
  isActive 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      if (isActive) {
        // Draw frequency bars
        const barCount = 20;
        const barWidth = canvas.width / barCount;
        
        for (let i = 0; i < barCount; i++) {
          const height = audioLevel * canvas.height * (1 - i / barCount);
          const hue = (i / barCount) * 120; // Green to red gradient
          
          ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
          ctx.fillRect(
            i * barWidth + 2,
            canvas.height - height,
            barWidth - 4,
            height
          );
        }
      }
      
      requestAnimationFrame(draw);
    };
    
    draw();
  }, [audioLevel, isActive]);

  return (
    <canvas 
      ref={canvasRef}
      width={300}
      height={100}
      className="audio-visualizer-canvas"
    />
  );
};
```

Audio Quality Settings:
```typescript
const audioConfigurations = {
  low: {
    sampleRate: 22050,
    bitRate: 64000,
    mimeType: 'audio/webm;codecs=opus'
  },
  medium: {
    sampleRate: 44100,
    bitRate: 128000,
    mimeType: 'audio/webm;codecs=opus'
  },
  high: {
    sampleRate: 48000,
    bitRate: 192000,
    mimeType: 'audio/webm;codecs=opus'
  }
};

const getSupportedMimeType = (): string => {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4'
  ];
  
  return types.find(type => MediaRecorder.isTypeSupported(type)) || 'audio/webm';
};
```

Acceptance Criteria:
- Given a voice evaluation question
- When a user records their response
- Then the audio is captured with quality visualization and metadata

Testing Strategy:
- Unit tests: Component behavior and state management
- Integration tests: Audio recording and playback
- Performance tests: Recording latency <100ms
- Compatibility tests: Browser compatibility matrix

Dependencies:
- Web Audio API for audio processing
- MediaRecorder API for recording
- React hooks for state management
- Canvas API for visualization

Risks & Mitigations:
- Browser compatibility: Feature detection and fallbacks
- Permission issues: Clear user guidance and error handling
- Audio quality: Adaptive bitrate and compression
- File size limits: Compression and chunked upload
```

### **Story 13: Speech-to-Text Integration**

```
Technical Story: Whisper Speech-to-Text Integration for Voice Response Processing
Module: Abilities Evaluation - Audio Processing
Developer: ML/Backend Engineer
Estimated Time: 3 days

Technical Requirements:
- Integrate OpenAI Whisper API for speech-to-text conversion
- Implement real-time and batch processing modes
- Support multiple languages and accents
- Handle audio preprocessing and optimization
- Provide transcription confidence scores

Implementation Details:
Whisper Integration Service:
```python
class WhisperTranscriptionService:
    def __init__(self):
        self.whisper_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.audio_processor = AudioProcessor()
        self.confidence_estimator = TranscriptionConfidence()
        self.cache_service = RedisCache()
    
    async def transcribe_audio(
        self, 
        audio_blob: bytes, 
        language: str = "auto",
        mode: str = "realtime"
    ) -> TranscriptionResult:
        
        # Preprocess audio
        processed_audio = await self.audio_processor.preprocess(audio_blob)
        
        # Check cache first
        cache_key = f"transcription:{hash(processed_audio)}:{language}"
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return TranscriptionResult.from_dict(cached_result)
        
        try:
            # Call Whisper API
            response = await self.whisper_client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", processed_audio, "audio/wav"),
                language=language if language != "auto" else None,
                response_format="verbose_json",
                temperature=0.0
            )
            
            # Calculate confidence
            confidence = await self.confidence_estimator.calculate(
                response.text, 
                processed_audio
            )
            
            result = TranscriptionResult(
                text=response.text,
                language=response.language,
                confidence=confidence,
                duration=response.duration,
                words=response.words if hasattr(response, 'words') else None,
                processing_time=time.time()
            )
            
            # Cache result
            await self.cache_service.setex(
                cache_key, 
                3600,  # 1 hour cache
                result.to_dict()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            # Fallback to local model if available
            return await self.fallback_transcription(processed_audio, language)
    
    async def batch_transcribe(
        self, 
        audio_files: List[bytes], 
        language: str = "auto"
    ) -> List[TranscriptionResult]:
        
        # Process in parallel with rate limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def transcribe_single(audio_blob: bytes) -> TranscriptionResult:
            async with semaphore:
                return await self.transcribe_audio(audio_blob, language, "batch")
        
        tasks = [transcribe_single(audio) for audio in audio_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if isinstance(r, TranscriptionResult)]
```

Audio Preprocessing Pipeline:
```python
class AudioProcessor:
    def __init__(self):
        self.target_sample_rate = 16000  # Whisper optimal
        self.target_channels = 1  # Mono
        self.max_duration = 30  # Max 30 seconds
    
    async def preprocess(self, audio_blob: bytes) -> bytes:
        # Load audio with librosa
        y, sr = librosa.load(io.BytesIO(audio_blob), sr=None)
        
        # Convert to mono if needed
        if len(y.shape) > 1:
            y = librosa.to_mono(y)
        
        # Resample to target sample rate
        if sr != self.target_sample_rate:
            y = librosa.resample(y, orig_sr=sr, target_sr=self.target_sample_rate)
        
        # Trim silence
        y, _ = librosa.effects.trim(y, top_db=20)
        
        # Limit duration
        if len(y) > self.target_sample_rate * self.max_duration:
            y = y[:self.target_sample_rate * self.max_duration]
        
        # Normalize audio
        y = librosa.util.normalize(y)
        
        # Convert back to bytes
        output_buffer = io.BytesIO()
        sf.write(output_buffer, y, self.target_sample_rate, format='WAV')
        return output_buffer.getvalue()
    
    def optimize_for_whisper(self, audio_data: bytes) -> bytes:
        # Apply noise reduction if needed
        # Enhance speech frequencies
        # Compress dynamic range
        return audio_data  # Placeholder for optimization
```

Confidence Estimation:
```python
class TranscriptionConfidence:
    def __init__(self):
        self.language_model = self.load_language_model()
    
    async def calculate(
        self, 
        transcription: str, 
        original_audio: bytes
    ) -> float:
        
        # Method 1: Whisper's internal confidence (if available)
        whisper_confidence = self.extract_whisper_confidence(transcription)
        
        # Method 2: Language model probability
        lm_score = self.calculate_language_model_score(transcription)
        
        # Method 3: Audio-phoneme alignment
        alignment_score = self.calculate_alignment_score(
            transcription, original_audio
        )
        
        # Combine scores with weights
        combined_confidence = (
            0.4 * whisper_confidence +
            0.3 * lm_score +
            0.3 * alignment_score
        )
        
        return min(max(combined_confidence, 0.0), 1.0)
    
    def calculate_language_model_score(self, text: str) -> float:
        # Calculate perplexity or probability of the text
        tokens = self.language_model.tokenize(text)
        log_prob = sum(self.language_model.score(token) for token in tokens)
        perplexity = math.exp(-log_prob / len(tokens))
        
        # Convert perplexity to confidence (lower perplexity = higher confidence)
        return 1.0 / (1.0 + perplexity / 100.0)
```

Database Schema:
```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    audio_file_path VARCHAR(255),
    transcription_text TEXT,
    language VARCHAR(10),
    confidence FLOAT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transcription_cache (
    audio_hash VARCHAR(64) PRIMARY KEY,
    transcription_text TEXT,
    language VARCHAR(10),
    confidence FLOAT,
    cached_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given a voice recording from the interface
- When the transcription service processes it
- Then accurate text is generated with confidence scores

Testing Strategy:
- Unit tests: Individual processing components
- Integration tests: End-to-end transcription flow
- Accuracy tests: Word Error Rate (WER) <5%
- Performance tests: Processing time <audio duration * 2

Dependencies:
- OpenAI Whisper API
- librosa for audio processing
- Redis for caching
- PostgreSQL for storage

Risks & Mitigations:
- API rate limits: Request queuing and caching
- Accuracy issues: Multiple confidence methods
- Audio quality: Preprocessing and optimization
- Cost management: Efficient caching and batching
```

### **Story 14: Multimodal Fusion Algorithm**

```
Technical Story: Multimodal Fusion Algorithm for Comprehensive Abilities Scoring
Module: Abilities Evaluation - Fusion Engine
Developer: ML/Backend Engineer
Estimated Time: 3 days

Technical Requirements:
- Implement fusion of text and voice evaluation results
- Create weighted scoring algorithm for multimodal data
- Handle missing or incomplete modalities
- Provide explainability for fusion decisions
- Support dynamic weight adjustment based on data quality

Implementation Details:
Multimodal Fusion Engine:
```python
class MultimodalFusionEngine:
    def __init__(self):
        self.text_weight = 0.6
        self.voice_weight = 0.4
        self.quality_calculator = DataQualityCalculator()
        self.explainer = FusionExplainer()
        self.confidence_estimator = FusionConfidence()
    
    def fuse_abilities_scores(
        self,
        text_scores: TextAbilitiesScores,
        voice_scores: VoiceAbilitiesScores,
        user_metadata: UserMetadata
    ) -> FusedAbilitiesScores:
        
        # Calculate data quality for each modality
        text_quality = self.quality_calculator.calculate_text_quality(
            text_scores, user_metadata
        )
        voice_quality = self.quality_calculator.calculate_voice_quality(
            voice_scores, user_metadata
        )
        
        # Dynamic weight adjustment based on quality
        adjusted_weights = self.adjust_weights_by_quality(
            text_quality, voice_quality
        )
        
        # Fusion algorithm
        fused_scores = self.perform_fusion(
            text_scores, 
            voice_scores, 
            adjusted_weights
        )
        
        # Calculate overall confidence
        overall_confidence = self.confidence_estimator.calculate(
            fused_scores, text_quality, voice_quality
        )
        
        # Generate explanations
        explanations = self.explainer.explain_fusion(
            text_scores, voice_scores, fused_scores, adjusted_weights
        )
        
        return FusedAbilitiesScores(
            logical_reasoning=fused_scores.logical_reasoning,
            analytical_thinking=fused_scores.analytical_thinking,
            verbal_reasoning=fused_scores.verbal_reasoning,
            overall_score=fused_scores.overall_score,
            confidence=overall_confidence,
            modality_weights=adjusted_weights,
            explanations=explanations,
            quality_scores={
                'text': text_quality,
                'voice': voice_quality
            }
        )
    
    def adjust_weights_by_quality(
        self, 
        text_quality: float, 
        voice_quality: float
    ) -> Dict[str, float]:
        
        # Calculate quality ratio
        total_quality = text_quality + voice_quality
        if total_quality == 0:
            return {'text': 0.5, 'voice': 0.5}  # Equal weights if no quality data
        
        # Adjust weights proportionally to quality
        text_ratio = text_quality / total_quality
        voice_ratio = voice_quality / total_quality
        
        # Apply smoothing to avoid extreme weights
        min_weight = 0.2
        max_weight = 0.8
        
        adjusted_text_weight = max(min_weight, min(max_weight, text_ratio))
        adjusted_voice_weight = 1.0 - adjusted_text_weight
        
        return {
            'text': adjusted_text_weight,
            'voice': adjusted_voice_weight
        }
    
    def perform_fusion(
        self,
        text_scores: TextAbilitiesScores,
        voice_scores: VoiceAbilitiesScores,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        
        fused = {}
        
        # Fuse each ability dimension
        for dimension in ['logical_reasoning', 'analytical_thinking', 'verbal_reasoning']:
            text_score = getattr(text_scores, dimension, 0)
            voice_score = getattr(voice_scores, dimension, 0)
            
            # Weighted fusion
            fused[dimension] = (
                weights['text'] * text_score + 
                weights['voice'] * voice_score
            )
        
        # Calculate overall score
        fused['overall_score'] = sum(fused.values()) / len(fused)
        
        return fused
```

Data Quality Assessment:
```python
class DataQualityCalculator:
    def calculate_text_quality(
        self, 
        text_scores: TextAbilitiesScores, 
        metadata: UserMetadata
    ) -> float:
        
        quality_factors = []
        
        # Response completeness
        completeness = self.calculate_completeness(text_scores)
        quality_factors.append(completeness)
        
        # Response time analysis
        time_quality = self.analyze_response_times(text_scores)
        quality_factors.append(time_quality)
        
        # Consistency across questions
        consistency = self.calculate_consistency(text_scores)
        quality_factors.append(consistency)
        
        # Language quality (grammar, coherence)
        language_quality = self.assess_language_quality(text_scores)
        quality_factors.append(language_quality)
        
        # Weighted average
        return sum(quality_factors) / len(quality_factors)
    
    def calculate_voice_quality(
        self, 
        voice_scores: VoiceAbilitiesScores, 
        metadata: UserMetadata
    ) -> float:
        
        quality_factors = []
        
        # Audio quality (signal-to-noise ratio)
        audio_quality = self.assess_audio_quality(voice_scores)
        quality_factors.append(audio_quality)
        
        # Transcription confidence
        transcription_confidence = voice_scores.average_transcription_confidence
        quality_factors.append(transcription_confidence)
        
        # Speech clarity and fluency
        speech_clarity = self.analyze_speech_clarity(voice_scores)
        quality_factors.append(speech_clarity)
        
        # Response completeness
        completeness = self.calculate_voice_completeness(voice_scores)
        quality_factors.append(completeness)
        
        return sum(quality_factors) / len(quality_factors)
```

Fusion Explainability:
```python
class FusionExplainer:
    def explain_fusion(
        self,
        text_scores: TextAbilitiesScores,
        voice_scores: VoiceAbilitiesScores,
        fused_scores: Dict[str, float],
        weights: Dict[str, float]
    ) -> FusionExplanation:
        
        explanations = {}
        
        for dimension in ['logical_reasoning', 'analytical_thinking', 'verbal_reasoning']:
            text_contrib = weights['text'] * getattr(text_scores, dimension, 0)
            voice_contrib = weights['voice'] * getattr(voice_scores, dimension, 0)
            
            explanations[dimension] = DimensionExplanation(
                final_score=fused_scores[dimension],
                text_contribution=text_contrib,
                voice_contribution=voice_contrib,
                reasoning=self.generate_reasoning(
                    text_scores, voice_scores, dimension, weights
                )
            )
        
        return FusionExplanation(
            dimension_explanations=explanations,
            modality_weights=weights,
            overall_reasoning=self.generate_overall_reasoning(
                text_scores, voice_scores, weights
            )
        )
    
    def generate_reasoning(
        self,
        text_scores: TextAbilitiesScores,
        voice_scores: VoiceAbilitiesScores,
        dimension: str,
        weights: Dict[str, float]
    ) -> str:
        
        text_score = getattr(text_scores, dimension, 0)
        voice_score = getattr(voice_scores, dimension, 0)
        
        reasoning_parts = []
        
        if text_score > voice_score:
            reasoning_parts.append(
                f"Text-based evaluation showed stronger performance ({text_score:.2f}) "
                f"compared to voice evaluation ({voice_score:.2f})"
            )
        else:
            reasoning_parts.append(
                f"Voice-based evaluation indicated higher ability ({voice_score:.2f}) "
                f"than text evaluation ({text_score:.2f})"
            )
        
        if weights['text'] > weights['voice']:
            reasoning_parts.append(
                "Greater emphasis was placed on text-based responses due to higher data quality"
            )
        else:
            reasoning_parts.append(
                "Voice responses were given more weight due to better audio quality and clarity"
            )
        
        return " ".join(reasoning_parts)
```

Acceptance Criteria:
- Given completed text and voice evaluations
- When the fusion algorithm processes results
- Then a comprehensive abilities score is generated with explanations

Testing Strategy:
- Unit tests: Individual fusion components
- Integration tests: Complete multimodal pipeline
- Accuracy tests: Fusion validation against expert ratings
- Performance tests: Fusion processing <200ms

Dependencies:
- NumPy/SciPy for mathematical computations
- Scikit-learn for quality assessment
- PostgreSQL for score storage
- Redis for caching intermediate results

Risks & Mitigations:
- Modality imbalance: Dynamic weight adjustment
- Quality assessment errors: Multiple quality metrics
- Fusion bias: Regular validation and calibration
- Performance issues: Efficient algorithms and caching
```

## Development Story Summary

| Story | Module | Developer | Time | Dependencies |
|-------|--------|-----------|------|-------------|
| Repository Setup | Infrastructure | Full Stack DevOps | 2 days | Git provider, Node.js, Python |
| CI/CD Pipeline | DevOps | DevOps Engineer | 3 days | GitHub Actions, Cloud provider |
| Cloud Infrastructure | Cloud | Cloud Architect | 3 days | Terraform, AWS/GCP/Azure |
| Database Schema | Database | Backend Engineer | 2 days | PostgreSQL, Migration tool |
| Dev Environment | Development | Full Stack | 2 days | Docker, Docker Compose |
| NLP CV Analysis | Knowledge - NLP | ML/NLP Engineer | 3 days | spaCy, Transformers, ESCO |
| ESCO Integration | Knowledge - API | Backend Integration | 2 days | ESCO/O*NET APIs, Redis |
| Adaptive Quiz | Knowledge - Quiz | Backend/ML Engineer | 3 days | IRT models, PostgreSQL |
| Knowledge Scoring | Knowledge - Scoring | Backend/ML Engineer | 2 days | NumPy, PostgreSQL |
| Frontend Interface | Knowledge - UI | Frontend Engineer | 2 days | React, Recharts, Redux |
| Text Cognitive Tests | Abilities - Text | Backend/ML Engineer | 3 days | NumPy, NLTK, PostgreSQL |
| Voice Recording | Abilities - Voice | Frontend Engineer | 2 days | Web Audio API, React |
| Speech-to-Text | Abilities - STT | ML/Backend Engineer | 3 days | Whisper API, librosa |
| Multimodal Fusion | Abilities - Fusion | ML/Backend Engineer | 3 days | NumPy, Scikit-learn |

**Total Estimated Time: 36 days (Sprint 0-6)**

### **Story 15: Mini-Projects Evaluation**

```
Technical Story: Mini-Projects Evaluation System for Practical Skills Assessment
Module: Skills Evaluation - Project Assessment
Developer: Backend/ML Engineer
Estimated Time: 3 days

Technical Requirements:
- Create mini-project templates for technical skills evaluation
- Implement automated project submission and evaluation pipeline
- Support multiple programming languages and frameworks
- Provide detailed scoring rubric with code quality metrics
- Enable peer review and expert validation components

Implementation Details:
Project Evaluation Framework:
```python
class MiniProjectEvaluator:
    def __init__(self):
        self.project_generator = ProjectGenerator()
        self.code_analyzer = CodeAnalyzer()
        self.test_runner = AutomatedTestRunner()
        self.quality_assessor = CodeQualityAssessor()
        self.plagiarism_detector = PlagiarismDetector()
    
    def create_project_assignment(
        self, 
        skill_domain: str, 
        difficulty: float,
        user_level: str
    ) -> ProjectAssignment:
        
        # Generate project based on skill requirements
        project = self.project_generator.generate(
            domain=skill_domain,
            difficulty=difficulty,
            user_level=user_level
        )
        
        # Create evaluation rubric
        rubric = self.create_evaluation_rubric(project, skill_domain)
        
        # Setup automated tests
        test_suite = self.test_runner.create_test_suite(project)
        
        return ProjectAssignment(
            id=uuid.uuid4(),
            project=project,
            rubric=rubric,
            test_suite=test_suite,
            time_limit=self.calculate_time_limit(difficulty),
            submission_requirements=self.get_requirements(skill_domain)
        )
    
    def evaluate_submission(
        self, 
        submission: ProjectSubmission
    ) -> ProjectEvaluation:
        
        # Run automated tests
        test_results = self.test_runner.run_tests(
            submission.code, 
            submission.project.test_suite
        )
        
        # Analyze code quality
        quality_metrics = self.quality_assessor.analyze(submission.code)
        
        # Check for plagiarism
        plagiarism_score = self.plagiarism_detector.check(submission.code)
        
        # Evaluate against rubric
        rubric_scores = self.evaluate_rubric(submission, quality_metrics)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(
            test_results, quality_metrics, rubric_scores, plagiarism_score
        )
        
        return ProjectEvaluation(
            test_results=test_results,
            quality_metrics=quality_metrics,
            rubric_scores=rubric_scores,
            plagiarism_score=plagiarism_score,
            overall_score=overall_score,
            feedback=self.generate_feedback(submission, overall_score),
            recommendations=self.generate_recommendations(submission)
        )
    
    def create_evaluation_rubric(
        self, 
        project: Project, 
        skill_domain: str
    ) -> EvaluationRubric:
        
        criteria = {
            'functionality': {
                'weight': 0.4,
                'description': 'Code meets functional requirements',
                'levels': self.create_functionality_levels(project)
            },
            'code_quality': {
                'weight': 0.3,
                'description': 'Clean, maintainable code',
                'levels': self.create_quality_levels(skill_domain)
            },
            'problem_solving': {
                'weight': 0.2,
                'description': 'Effective problem-solving approach',
                'levels': self.create_problem_solving_levels(project)
            },
            'documentation': {
                'weight': 0.1,
                'description': 'Clear documentation and comments',
                'levels': self.create_documentation_levels()
            }
        }
        
        return EvaluationRubric(criteria=criteria)
```

Project Templates by Skill Domain:
```python
class ProjectGenerator:
    def __init__(self):
        self.templates = {
            'web_development': [
                {
                    'title': 'RESTful API Builder',
                    'description': 'Build a REST API for task management',
                    'requirements': [
                        'CRUD operations for tasks',
                        'User authentication',
                        'Input validation',
                        'Error handling',
                        'API documentation'
                    ],
                    'technologies': ['Node.js', 'Express', 'MongoDB'],
                    'estimated_hours': 8
                },
                {
                    'title': 'React Dashboard',
                    'description': 'Create an interactive dashboard with data visualization',
                    'requirements': [
                        'Responsive design',
                        'Data charts and graphs',
                        'Real-time updates',
                        'User preferences',
                        'Export functionality'
                    ],
                    'technologies': ['React', 'Chart.js', 'WebSocket'],
                    'estimated_hours': 10
                }
            ],
            'data_science': [
                {
                    'title': 'Customer Segmentation',
                    'description': 'Analyze customer data and create segmentation model',
                    'requirements': [
                        'Data preprocessing',
                        'Clustering algorithm',
                        'Visualization of results',
                        'Model evaluation',
                        'Documentation of methodology'
                    ],
                    'technologies': ['Python', 'scikit-learn', 'pandas', 'matplotlib'],
                    'estimated_hours': 12
                }
            ],
            'mobile_development': [
                {
                    'title': 'Todo App',
                    'description': 'Build a mobile todo application with offline support',
                    'requirements': [
                        'CRUD operations',
                        'Offline data storage',
                        'Push notifications',
                        'User interface',
                        'Data synchronization'
                    ],
                    'technologies': ['React Native', 'AsyncStorage', 'Firebase'],
                    'estimated_hours': 10
                }
            ]
        }
    
    def generate(
        self, 
        domain: str, 
        difficulty: float, 
        user_level: str
    ) -> Project:
        
        # Select appropriate template
        templates = self.templates.get(domain, [])
        base_template = random.choice(templates)
        
        # Adjust complexity based on difficulty
        adjusted_requirements = self.adjust_complexity(
            base_template['requirements'], 
            difficulty
        )
        
        return Project(
            title=base_template['title'],
            description=base_template['description'],
            requirements=adjusted_requirements,
            technologies=base_template['technologies'],
            estimated_hours=int(base_template['estimated_hours'] * difficulty),
            difficulty=difficulty,
            skill_domain=domain
        )
```

Automated Testing Framework:
```python
class AutomatedTestRunner:
    def __init__(self):
        self.test_environments = {
            'javascript': NodeJSTestEnvironment(),
            'python': PythonTestEnvironment(),
            'java': JavaTestEnvironment(),
            'react': ReactTestEnvironment()
        }
    
    def create_test_suite(self, project: Project) -> TestSuite:
        # Generate tests based on project requirements
        functional_tests = self.generate_functional_tests(project)
        performance_tests = self.generate_performance_tests(project)
        security_tests = self.generate_security_tests(project)
        
        return TestSuite(
            functional=functional_tests,
            performance=performance_tests,
            security=security_tests,
            setup_instructions=self.get_setup_instructions(project)
        )
    
    def run_tests(
        self, 
        submission_code: str, 
        test_suite: TestSuite
    ) -> TestResults:
        
        # Detect programming language
        language = self.detect_language(submission_code)
        test_env = self.test_environments.get(language)
        
        if not test_env:
            raise UnsupportedLanguageError(f"Language {language} not supported")
        
        # Setup test environment
        test_env.setup(submission_code, test_suite.setup_instructions)
        
        # Run functional tests
        functional_results = test_env.run_functional_tests(test_suite.functional)
        
        # Run performance tests
        performance_results = test_env.run_performance_tests(test_suite.performance)
        
        # Run security tests
        security_results = test_env.run_security_tests(test_suite.security)
        
        return TestResults(
            functional=functional_results,
            performance=performance_results,
            security=security_results,
            overall_score=self.calculate_test_score(
                functional_results, performance_results, security_results
            )
        )
```

Database Schema:
```sql
CREATE TABLE mini_projects (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    skill_domain VARCHAR(100),
    difficulty FLOAT,
    requirements JSONB,
    technologies TEXT[],
    estimated_hours INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE project_submissions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    project_id UUID REFERENCES mini_projects(id),
    code TEXT,
    submission_url VARCHAR(255),
    submitted_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'submitted'
);

CREATE TABLE project_evaluations (
    id UUID PRIMARY KEY,
    submission_id UUID REFERENCES project_submissions(id),
    test_results JSONB,
    quality_metrics JSONB,
    rubric_scores JSONB,
    plagiarism_score FLOAT,
    overall_score FLOAT,
    feedback TEXT,
    evaluated_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given a mini-project assignment
- When a user submits their solution
- Then the system provides comprehensive evaluation with detailed feedback

Testing Strategy:
- Unit tests: Individual evaluation components
- Integration tests: Complete evaluation pipeline
- Accuracy tests: Score validation against expert evaluations
- Performance tests: Evaluation processing <5 minutes

Dependencies:
- Docker containers for isolated testing environments
- Code analysis tools (ESLint, Pylint, SonarQube)
- Testing frameworks (Jest, pytest, JUnit)
- Plagiarism detection APIs

Risks & Mitigations:
- Code plagiarism: Multiple detection methods
- Environment setup issues: Containerized testing
- Subjective evaluation: Clear rubrics and automated scoring
- Performance bottlenecks: Async processing and queuing
```

### **Story 16: GitHub API Integration**

```
Technical Story: GitHub API Integration for Portfolio Analysis and Skills Assessment
Module: Skills Evaluation - External Integration
Developer: Backend Integration Engineer
Estimated Time: 2 days

Technical Requirements:
- Integrate GitHub API for repository access and analysis
- Implement OAuth authentication for GitHub access
- Support both public and private repository analysis
- Handle API rate limiting and caching strategies
- Extract relevant metrics for skills assessment

Implementation Details:
GitHub Integration Service:
```python
class GitHubIntegrationService:
    def __init__(self):
        self.github_client = None
        self.cache_service = RedisCache()
        self.rate_limiter = GitHubRateLimiter()
        self.analyzer = GitHubAnalyzer()
    
    async def authenticate_user(self, access_token: str) -> GitHubUser:
        try:
            # Initialize GitHub client with access token
            self.github_client = AsyncGitHubClient(access_token)
            
            # Get user information
            user_data = await self.github_client.get_user()
            
            # Store authentication securely
            await self.store_user_tokens(user_data['id'], access_token)
            
            return GitHubUser(
                id=user_data['id'],
                username=user_data['login'],
                name=user_data['name'],
                email=user_data['email'],
                avatar_url=user_data['avatar_url'],
                public_repos=user_data['public_repos'],
                followers=user_data['followers'],
                following=user_data['following']
            )
            
        except GitHubAuthenticationError as e:
            logger.error(f"GitHub authentication failed: {e}")
            raise
    
    async def analyze_user_portfolio(
        self, 
        user_id: UUID,
        analysis_depth: str = 'standard'
    ) -> PortfolioAnalysis:
        
        # Get user's repositories
        repositories = await self.get_user_repositories(user_id, analysis_depth)
        
        # Analyze each repository
        repo_analyses = []
        for repo in repositories:
            analysis = await self.analyze_repository(repo, analysis_depth)
            repo_analyses.append(analysis)
        
        # Calculate overall portfolio metrics
        portfolio_metrics = self.calculate_portfolio_metrics(repo_analyses)
        
        # Identify technical skills
        technical_skills = self.identify_technical_skills(repo_analyses)
        
        # Assess development patterns
        development_patterns = self.analyze_development_patterns(repo_analyses)
        
        return PortfolioAnalysis(
            repositories=repo_analyses,
            portfolio_metrics=portfolio_metrics,
            technical_skills=technical_skills,
            development_patterns=development_patterns,
            analysis_depth=analysis_depth,
            analyzed_at=datetime.now()
        )
    
    async def get_user_repositories(
        self, 
        user_id: UUID, 
        analysis_depth: str
    ) -> List[GitHubRepository]:
        
        # Check cache first
        cache_key = f"user_repos:{user_id}:{analysis_depth}"
        cached_repos = await self.cache_service.get(cache_key)
        if cached_repos:
            return [GitHubRepository.from_dict(repo) for repo in cached_repos]
        
        try:
            # Apply rate limiting
            await self.rate_limiter.wait_if_needed()
            
            # Get repositories based on analysis depth
            if analysis_depth == 'basic':
                repos_data = await self.github_client.get_user_repos(
                    type='public', 
                    per_page=50
                )
            elif analysis_depth == 'standard':
                repos_data = await self.github_client.get_user_repos(
                    type='all', 
                    per_page=100
                )
            else:  # comprehensive
                repos_data = await self.github_client.get_user_repos(
                    type='all', 
                    per_page=100
                )
                # Include private repos if permissions allow
                repos_data.extend(await self.get_private_repos())
            
            repositories = []
            for repo_data in repos_data:
                repo = GitHubRepository(
                    id=repo_data['id'],
                    name=repo_data['name'],
                    full_name=repo_data['full_name'],
                    description=repo_data.get('description', ''),
                    language=repo_data.get('language', ''),
                    stars=repo_data['stargazers_count'],
                    forks=repo_data['forks_count'],
                    open_issues=repo_data['open_issues_count'],
                    created_at=repo_data['created_at'],
                    updated_at=repo_data['updated_at'],
                    pushed_at=repo_data['pushed_at'],
                    size=repo_data['size'],
                    is_private=repo_data['private'],
                    default_branch=repo_data['default_branch']
                )
                repositories.append(repo)
            
            # Cache results
            await self.cache_service.setex(
                cache_key, 
                3600,  # 1 hour cache
                [repo.to_dict() for repo in repositories]
            )
            
            return repositories
            
        except GitHubAPIError as e:
            logger.error(f"Failed to get repositories: {e}")
            raise
    
    async def analyze_repository(
        self, 
        repository: GitHubRepository, 
        analysis_depth: str
    ) -> RepositoryAnalysis:
        
        try:
            # Get repository content
            content = await self.get_repository_content(repository, analysis_depth)
            
            # Analyze code structure
            code_structure = await self.analyzer.analyze_code_structure(
                content, repository.language
            )
            
            # Get commit history
            commit_history = await self.get_commit_history(repository, analysis_depth)
            
            # Analyze contributions
            contributions = await self.analyze_contributions(repository, analysis_depth)
            
            # Check for documentation
            documentation = await self.analyze_documentation(content)
            
            # Identify dependencies and technologies
            technologies = await self.identify_technologies(content)
            
            return RepositoryAnalysis(
                repository=repository,
                code_structure=code_structure,
                commit_history=commit_history,
                contributions=contributions,
                documentation=documentation,
                technologies=technologies,
                quality_metrics=self.calculate_quality_metrics(
                    code_structure, commit_history, documentation
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze repository {repository.name}: {e}")
            return RepositoryAnalysis(
                repository=repository,
                error=str(e)
            )
```

GitHub Rate Limiting and Caching:
```python
class GitHubRateLimiter:
    def __init__(self):
        self.rate_limit_info = {
            'remaining': 5000,  # Default for authenticated requests
            'reset_time': None,
            'limit': 5000
        }
        self.request_times = deque(maxlen=100)
    
    async def wait_if_needed(self):
        current_time = time.time()
        
        # Update rate limit info if needed
        if self.rate_limit_info['reset_time'] and current_time > self.rate_limit_info['reset_time']:
            self.rate_limit_info['remaining'] = self.rate_limit_info['limit']
        
        # Check if we need to wait
        if self.rate_limit_info['remaining'] < 10:
            wait_time = self.rate_limit_info['reset_time'] - current_time
            if wait_time > 0:
                await asyncio.sleep(wait_time + 1)  # Add buffer
        
        # Track request time
        self.request_times.append(current_time)
        
        # Simple rate limiting: max 100 requests per minute
        recent_requests = [t for t in self.request_times if current_time - t < 60]
        if len(recent_requests) >= 100:
            await asyncio.sleep(60 - (current_time - recent_requests[0]))
    
    def update_rate_limit(self, headers: dict):
        self.rate_limit_info['remaining'] = int(headers.get('X-RateLimit-Remaining', 0))
        self.rate_limit_info['limit'] = int(headers.get('X-RateLimit-Limit', 5000))
        self.rate_limit_info['reset_time'] = int(headers.get('X-RateLimit-Reset', 0))
```

OAuth Authentication Flow:
```python
class GitHubOAuthHandler:
    def __init__(self):
        self.client_id = os.getenv('GITHUB_CLIENT_ID')
        self.client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GITHUB_REDIRECT_URI')
    
    def get_authorization_url(self, state: str) -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'user repo',  # Request user and repository access
            'state': state
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> str:
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'state': state
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://github.com/login/oauth/access_token',
                data=data,
                headers={'Accept': 'application/json'}
            ) as response:
                result = await response.json()
                
                if 'error' in result:
                    raise GitHubOAuthError(result['error_description'])
                
                return result['access_token']
```

Database Schema:
```sql
CREATE TABLE github_integrations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    github_user_id INTEGER UNIQUE,
    username VARCHAR(255),
    access_token_encrypted TEXT,
    token_expires_at TIMESTAMP,
    scope TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portfolio_analyses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    analysis_data JSONB,
    technical_skills JSONB,
    portfolio_metrics JSONB,
    analysis_depth VARCHAR(20),
    analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE repository_analyses (
    id UUID PRIMARY KEY,
    portfolio_analysis_id UUID REFERENCES portfolio_analyses(id),
    repository_id INTEGER,
    repository_name VARCHAR(255),
    analysis_data JSONB,
    quality_metrics JSONB,
    analyzed_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given user authorization for GitHub access
- When the integration service analyzes their portfolio
- Then comprehensive repository analysis is performed with skills extraction

Testing Strategy:
- Unit tests: Individual API integration components
- Integration tests: Complete GitHub analysis flow
- Performance tests: Analysis completion <2 minutes
- Security tests: Token encryption and secure storage

Dependencies:
- PyGitHub or GitHub GraphQL API
- Redis for caching and rate limiting
- Encryption library for token storage
- Async HTTP client (aiohttp)

Risks & Mitigations:
- API rate limits: Comprehensive rate limiting and caching
- Token security: Encryption and secure storage
- Private repository access: Proper permission handling
- Large repositories: Analysis depth limits and progress tracking
```

### **Story 17: Code Analysis Algorithm**

```
Technical Story: Advanced Code Analysis Algorithm for Skills Assessment and Quality Evaluation
Module: Skills Evaluation - Code Analysis
Developer: ML/Backend Engineer
Estimated Time: 3 days

Technical Requirements:
- Implement multi-language code analysis for quality assessment
- Create skill extraction algorithms from code patterns
- Develop complexity metrics and best practices evaluation
- Support real-time analysis and batch processing
- Provide detailed feedback and improvement recommendations

Implementation Details:
Code Analysis Engine:
```python
class CodeAnalysisEngine:
    def __init__(self):
        self.language_analyzers = {
            'javascript': JavaScriptAnalyzer(),
            'python': PythonAnalyzer(),
            'java': JavaAnalyzer(),
            'typescript': TypeScriptAnalyzer(),
            'react': ReactAnalyzer()
        }
        self.quality_calculator = CodeQualityCalculator()
        self.skill_extractor = SkillExtractor()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.pattern_detector = PatternDetector()
    
    def analyze_code(
        self, 
        code: str, 
        language: str,
        analysis_type: str = 'comprehensive'
    ) -> CodeAnalysis:
        
        # Get language-specific analyzer
        analyzer = self.language_analyzers.get(language.lower())
        if not analyzer:
            raise UnsupportedLanguageError(f"Language {language} not supported")
        
        # Parse code structure
        ast = analyzer.parse_code(code)
        
        # Analyze code quality
        quality_metrics = self.quality_calculator.calculate(ast, code)
        
        # Extract technical skills
        technical_skills = self.skill_extractor.extract(ast, language)
        
        # Calculate complexity metrics
        complexity_metrics = self.complexity_analyzer.calculate(ast)
        
        # Detect design patterns
        design_patterns = self.pattern_detector.detect(ast, language)
        
        # Identify best practices
        best_practices = analyzer.check_best_practices(ast, code)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            quality_metrics, complexity_metrics, best_practices
        )
        
        return CodeAnalysis(
            language=language,
            ast=ast,
            quality_metrics=quality_metrics,
            technical_skills=technical_skills,
            complexity_metrics=complexity_metrics,
            design_patterns=design_patterns,
            best_practices=best_practices,
            recommendations=recommendations,
            overall_score=self.calculate_overall_score(
                quality_metrics, complexity_metrics, best_practices
            )
        )
    
    def analyze_repository_structure(
        self, 
        repository_files: List[RepositoryFile]
    ) -> RepositoryStructureAnalysis:
        
        analyses = []
        skill_frequency = defaultdict(int)
        language_distribution = defaultdict(int)
        
        for file in repository_files:
            if file.language and file.language in self.language_analyzers:
                analysis = self.analyze_code(file.content, file.language)
                analyses.append(analysis)
                
                # Aggregate skills
                for skill in analysis.technical_skills:
                    skill_frequency[skill.name] += skill.confidence
                
                language_distribution[file.language] += 1
        
        # Calculate repository-level metrics
        repo_quality = self.calculate_repository_quality(analyses)
        repo_complexity = self.calculate_repository_complexity(analyses)
        
        # Identify architectural patterns
        architecture_patterns = self.identify_architecture_patterns(analyses)
        
        return RepositoryStructureAnalysis(
            file_analyses=analyses,
            skill_frequency=dict(skill_frequency),
            language_distribution=dict(language_distribution),
            repository_quality=repo_quality,
            repository_complexity=repo_complexity,
            architecture_patterns=architecture_patterns
        )
```

Language-Specific Analyzers:
```python
class JavaScriptAnalyzer:
    def __init__(self):
        self.esprima_parser = EsprimaParser()
        self.quality_checker = JavaScriptQualityChecker()
    
    def parse_code(self, code: str) -> AST:
        try:
            return self.esprima_parser.parse(code, {
                'sourceType': 'module',
                'ecmaVersion': 2022
            })
        except ParseError as e:
            raise CodeParseError(f"JavaScript parse error: {e}")
    
    def check_best_practices(self, ast: AST, code: str) -> List[BestPracticeViolation]:
        violations = []
        
        # Check for use strict
        if not self.has_use_strict(ast):
            violations.append(BestPracticeViolation(
                type='missing_use_strict',
                severity='warning',
                message='Missing "use strict" directive'
            ))
        
        # Check for var usage (prefer const/let)
        var_declarations = self.find_var_declarations(ast)
        for var_decl in var_declarations:
            violations.append(BestPracticeViolation(
                type='var_usage',
                severity='info',
                message=f'Consider using const/let instead of var at line {var_decl.line}'
            ))
        
        # Check for console.log in production code
        console_logs = self.find_console_logs(ast)
        for log in console_logs:
            violations.append(BestPracticeViolation(
                type='console_log',
                severity='warning',
                message=f'Remove console.log at line {log.line}'
            ))
        
        # Check function complexity
        functions = self.extract_functions(ast)
        for func in functions:
            if func.complexity > 10:
                violations.append(BestPracticeViolation(
                    type='high_complexity',
                    severity='error',
                    message=f'Function {func.name} has high complexity ({func.complexity})'
                ))
        
        return violations

class PythonAnalyzer:
    def __init__(self):
        self.ast_parser = ast.AST()
        self.quality_checker = PythonQualityChecker()
    
    def parse_code(self, code: str) -> AST:
        try:
            return ast.parse(code)
        except SyntaxError as e:
            raise CodeParseError(f"Python syntax error: {e}")
    
    def check_best_practices(self, ast_node: AST, code: str) -> List[BestPracticeViolation]:
        violations = []
        
        # Check for docstrings
        functions_classes = self.extract_functions_and_classes(ast_node)
        for item in functions_classes:
            if not self.has_docstring(item):
                violations.append(BestPracticeViolation(
                    type='missing_docstring',
                    severity='warning',
                    message=f'Missing docstring for {item.type} {item.name}'
                ))
        
        # Check import organization
        imports = self.extract_imports(ast_node)
        if not self.are_imports_organized(imports):
            violations.append(BestPracticeViolation(
                type='import_organization',
                severity='info',
                message='Imports should be organized (stdlib, third-party, local)'
            ))
        
        # Check line length
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 88:  # PEP 8 recommendation
                violations.append(BestPracticeViolation(
                    type='line_length',
                    severity='warning',
                    message=f'Line {i} exceeds 88 characters ({len(line)} chars)'
                ))
        
        return violations
```

Code Quality Metrics:
```python
class CodeQualityCalculator:
    def calculate(self, ast: AST, code: str) -> CodeQualityMetrics:
        
        # Calculate maintainability index
        maintainability = self.calculate_maintainability_index(ast, code)
        
        # Calculate technical debt
        technical_debt = self.calculate_technical_debt(ast, code)
        
        # Calculate test coverage (if tests available)
        test_coverage = self.calculate_test_coverage(ast, code)
        
        # Calculate code duplication
        duplication = self.calculate_duplication(code)
        
        # Calculate security issues
        security_issues = self.identify_security_issues(ast, code)
        
        return CodeQualityMetrics(
            maintainability_index=maintainability,
            technical_debt_hours=technical_debt,
            test_coverage_percentage=test_coverage,
            duplication_percentage=duplication,
            security_issues_count=len(security_issues),
            security_issues=security_issues,
            overall_quality_score=self.calculate_quality_score(
                maintainability, technical_debt, test_coverage, duplication
            )
        )
    
    def calculate_maintainability_index(self, ast: AST, code: str) -> float:
        # Calculate cyclomatic complexity
        complexity = self.calculate_cyclomatic_complexity(ast)
        
        # Calculate lines of code
        loc = len([line for line in code.split('\n') if line.strip()])
        
        # Calculate volume (Halstead metrics)
        volume = self.calculate_halstead_volume(ast)
        
        # Maintainability index formula (Microsoft)
        maintainability = max(0, (
            171 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(loc)
        )) * 100 / 171
        
        return maintainability
    
    def calculate_cyclomatic_complexity(self, ast: AST) -> int:
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_points = self.count_decision_points(ast)
        complexity += decision_points
        
        return complexity
```

Skill Extraction Algorithm:
```python
class SkillExtractor:
    def __init__(self):
        self.skill_patterns = self.load_skill_patterns()
        self.framework_detectors = self.load_framework_detectors()
        self.library_detectors = self.load_library_detectors()
    
    def extract(self, ast: AST, language: str) -> List[TechnicalSkill]:
        skills = []
        
        # Extract framework skills
        framework_skills = self.extract_framework_skills(ast, language)
        skills.extend(framework_skills)
        
        # Extract library skills
        library_skills = self.extract_library_skills(ast, language)
        skills.extend(library_skills)
        
        # Extract language features
        language_features = self.extract_language_features(ast, language)
        skills.extend(language_features)
        
        # Extract design pattern skills
        pattern_skills = self.extract_pattern_skills(ast, language)
        skills.extend(pattern_skills)
        
        # Calculate skill levels based on complexity and usage
        for skill in skills:
            skill.level = self.calculate_skill_level(skill, ast)
            skill.confidence = self.calculate_confidence(skill, ast)
        
        return skills
    
    def extract_framework_skills(self, ast: AST, language: str) -> List[TechnicalSkill]:
        skills = []
        
        for detector in self.framework_detectors[language]:
            detected_skills = detector.detect(ast)
            skills.extend(detected_skills)
        
        return skills
    
    def calculate_skill_level(self, skill: TechnicalSkill, ast: AST) -> str:
        # Analyze usage complexity
        usage_complexity = self.analyze_usage_complexity(skill, ast)
        
        # Analyze implementation quality
        implementation_quality = self.analyze_implementation_quality(skill, ast)
        
        # Determine skill level
        if usage_complexity > 0.8 and implementation_quality > 0.8:
            return 'expert'
        elif usage_complexity > 0.6 and implementation_quality > 0.6:
            return 'advanced'
        elif usage_complexity > 0.4 and implementation_quality > 0.4:
            return 'intermediate'
        else:
            return 'beginner'
```

Database Schema:
```sql
CREATE TABLE code_analyses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    repository_id VARCHAR(255),
    file_path VARCHAR(500),
    language VARCHAR(50),
    quality_metrics JSONB,
    technical_skills JSONB,
    complexity_metrics JSONB,
    best_practices_violations JSONB,
    overall_score FLOAT,
    analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE technical_skills (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    language VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_skill_assessments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    skill_id UUID REFERENCES technical_skills(id),
    proficiency_level VARCHAR(20),
    confidence FLOAT,
    evidence_count INTEGER,
    last_assessed_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given source code in supported languages
- When the analysis engine processes it
- Then comprehensive quality metrics and skill assessments are generated

Testing Strategy:
- Unit tests: Individual analysis components
- Integration tests: Complete analysis pipeline
- Accuracy tests: Skill validation against expert assessments
- Performance tests: Analysis processing <30 seconds per file

Dependencies:
- AST parsers for each language (esprima, python-ast, etc.)
- Code quality tools (ESLint, Pylint, SonarQube APIs)
- Machine learning models for skill classification
- Static analysis frameworks

Risks & Mitigations:
- Parse errors: Robust error handling and fallbacks
- Language limitations: Progressive language support
- False positives: Multiple validation methods
- Performance issues: Async processing and caching
```

### **Story 18: Mapping KASH-Métiers**

```
Technical Story: Mapping KASH Competency Model to Métiers Ontology
Module: Skills Evaluation - Career Mapping
Developer: Backend/AI Engineer
Estimated Time: 3 days

Technical Requirements:
- Align the KASH competency dimensions with French métiers taxonomy (Pôle emploi, ROME)
- Build a translation layer between KASH profiles and ESCO/Métier codes
- Support fuzzy matching and weighting for partial overlaps
- Provide API to request recommended métiers per user profile
- Maintain provenance for each mapping decision for explainability

Implementation Details:
Mapping Graph Engine:
```python
class KashMetierMapper:
    def __init__(self, skill_embeddings: EmbeddingIndex):
        self.skill_embeddings = skill_embeddings
        self.ontology = MetierOntologyClient()
        self.explainability = MappingExplainability()
        self.cache = RedisCache()

    def map_profile(self, profile: KashProfile) -> List[MetierMapping]:
        cache_key = f"mapping:{profile.id}"
        cached = self.cache.get(cache_key)
        if cached:
            return [MetierMapping.from_dict(m) for m in cached]

        candidate_metiers = self.ontology.search(profile.primary_skills)
        mappings = []
        for metier in candidate_metiers:
            score = self.calculate_alignment(profile, metier)
            explanations = self.explainability.describe(profile, metier, score)
            mappings.append(
                MetierMapping(metadata=metier, score=score, explanations=explanations)
            )

        self.cache.setex(cache_key, 7200, [m.to_dict() for m in mappings])
        return mappings

    def calculate_alignment(self, profile: KashProfile, metier: MetierNode) -> float:
        profile_vector = self.skill_embeddings.encode(profile.skills)
        metier_vector = self.skill_embeddings.encode(metier.skills)
        return cosine_similarity(profile_vector, metier_vector)
```

Ontology Sync Job:
```python
@shared_task
def refresh_metier_graph():
    client = MetierOntologyClient()
    updated_nodes = client.fetch_latest()
    graph = MetierGraph()
    graph.upsert_nodes(updated_nodes)
    graph.persist()
```

Acceptance Criteria:
- Given a complete KASH profile
- When the mapping service executes
- Then at least 5 métiers are returned with confidence scores and explanations

Testing Strategy:
- Unit tests: Alignment scoring + caching
- Integration tests: Ontology sync + API responses
- Accuracy tests: Human expert validation sample
- Load tests: 200 mappings/s

Dependencies:
- Embedding service (e.g. OpenAI ada-002 or local sentence transformer)
- Metier ontology client (ESCO/ROME)
- Redis cache
- Task queue (Celery)

Risks & Mitigations:
- Ontology drift: Scheduled graph refresh
- Mapping hallucinations: Expert reviews + thresholds
- API latency: Precomputed mappings per persona
```

### **Story 19: Prediction & Success Probability Model**

```
Technical Story: Prediction Model for Success Probability in Career Paths
Module: Skills Evaluation - Predictive Analytics
Developer: Data Scientist
Estimated Time: 3 days

Technical Requirements:
- Train a model predicting likelihood of success for a given métier path
- Incorporate historical data (student profiles, outcomes, project scores)
- Provide feature importance for transparency
- Output probability, confidence, and recommended development steps
- Support batch and real-time scoring modes

Implementation Details:
SuccessProbabilityModel:
```python
class SuccessProbabilityModel:
    def __init__(self):
        self.model = XGBoostClassifier()
        self.preprocessor = FeatureAssembler()
        self.explainer = ShapExplainer(self.model)
        self.history_repo = SuccessHistoryRepository()

    def predict(self, profile: KashProfile) -> SuccessProbabilityOutcome:
        features = self.preprocessor.transform(profile)
        probability = self.model.predict_proba([features])[0][1]
        confidence = self.calculate_confidence(probability, profile)
        shap_values = self.explainer.shap_values(features)
        return SuccessProbabilityOutcome(
            probability=probability,
            confidence=confidence,
            explanations=self.explainer.format(shap_values)
        )

    def train(self):
        dataset = self.history_repo.load()
        features, labels = self.preprocessor.prepare(dataset)
        self.model.fit(features, labels)
        self.explainer.fit(features)
```

Confidence Calibration:
```python
def calculate_confidence(self, probability: float, profile: KashProfile) -> float:
    data_density = self.history_repo.get_density(profile)
    return probability * min(1.0, 1.0 + math.log1p(data_density))
```

Database Schema for outcomes:
```sql
CREATE TABLE success_predictions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    metier_code VARCHAR(50),
    probability FLOAT,
    confidence FLOAT,
    explanations JSONB,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given a KASH profile and target métier
- When the prediction service runs
- Then a probability with confidence and explanations is stored

Testing Strategy:
- Unit tests: Feature assembler + confidence function
- Integration tests: Full prediction + storage
- Accuracy tests: AUC-ROC > 0.85 on holdout
- Drift detection tests weekly

Dependencies:
- XGBoost or LightGBM
- Shap for explainability
- Historical outcomes dataset
- Model monitoring service

Risks & Mitigations:
- Data sparsity: Similarity-based augmentation
- Model drift: Retrain weekly + drift monitors
- Ethical bias: Disparate impact analysis
```

### **Story 20: IA Explicable Layer**

```
Technical Story: Explainable AI Layer for All KASH Reasoning Components
Module: Data Platform - Explainability
Developer: ML Engineer / DevOps
Estimated Time: 3 days

Technical Requirements:
- Capture decision paths from NLP, fusion, prediction modules
- Expose REST endpoint returning SHAP/Attention + human narrative
- Store explainability records for auditing
- Provide UI-friendly metadata (labels, severity)
- Support multi-language (FR/EN) narratives

Implementation Details:
Explainability Registry:
```python
class ExplainabilityRegistry:
    def __init__(self):
        self.storage = PostgresExplainabilityStore()
        self.template_engine = NarrativeGenerator()

    def register(self, event: ExplainabilityEvent):
        narrative = self.template_engine.generate(event)
        record = ExplainabilityRecord(
            component=event.component,
            explanation=narrative,
            metadata=event.metadata
        )
        self.storage.save(record)
        return record
```

REST API (FastAPI snippet):
```python
@router.get('/explain/{record_id}')
async def get_explanation(record_id: UUID):
    record = await explainability_store.fetch(record_id)
    return {
        'record': record,
        'human_narrative': record.explanation,
        'parts': record.metadata
    }
```

Ledger Schema:
```sql
CREATE TABLE explainability_records (
    id UUID PRIMARY KEY,
    component VARCHAR(100),
    explanation TEXT,
    metadata JSONB,
    source_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Acceptance Criteria:
- Given any KASH decision (e.g. fusion score)
- When explainability event is emitted
- Then a record with a human narrative plus metadata is persisted and retrievable

Testing Strategy:
- Unit tests: Template generation + storage
- Integration tests: API endpoints + triggered events
- Performance tests: Recording <10ms
- E2E tests: UI fetch and render

Dependencies:
- FastAPI or similar
- Database auditing schema
- Template engine (e.g., Jinja2)
- Logging/observability stack

Risks & Mitigations:
- Narrative mismatch: Guardrails + human review
- Storage growth: TTL + archiving
- Latency: Async event buffering
```

### **Story 21: Dashboard 4D Integration**

```
Technical Story: 4D Evaluation Dashboard Integration for Knowledge + Abilities + Skills + Habits
Module: Frontend - Evaluation Dashboard
Developer: Frontend Engineer
Estimated Time: 2 days

Technical Requirements:
- Visualize scores across the four KASH dimensions using Recharts/Three.js
- Support time-series comparison and goal tracking
- Allow exporting PDFs with personalized insights
- Fetch data via GraphQL/REST and show explainability highlights
- Enable real-time updates when new assessments arrive

Implementation Details:
Dashboard Layout:
```tsx
const Dashboard4D: React.FC = () => {
  const { data, loading } = useQuery(DASHBOARD_QUERY);
  const [exporting, setExporting] = useState(false);
  
  const radarData = useMemo(() => buildRadarData(data), [data]);

  return (
    <section className="dashboard-4d">
      <header>
        <h2>Évaluation 4D du KASH</h2>
        <Button onClick={() => exportPdf(data)} disabled={exporting}>Exporter</Button>
      </header>
      <div className="grid">
        <RadarChart data={radarData} />
        <TimeSeriesChart data={data.timeSeries} />
        <InsightsList insights={data.explainability} />
      </div>
    </section>
  );
};
```

Real-time Layer:
```tsx
const useDashboardSubscription = () => {
  useSubscription(DASHBOARD_SUBSCRIPTION, {
    onData: ({ data }) => {
      queryClient.setQueryData(DASHBOARD_QUERY_KEY, data.dashboard);
    }
  });
};
```

Acceptance Criteria:
- Given user data across modules
- When they open the dashboard
- Then they see synchronized 4D radar, timelines, and explainability plus can export insights

Testing Strategy:
- Unit tests: Chart helpers + export
- Integration tests: Data fetching + subscription flow
- Visual regression tests
- Accessibility tests: WCAG AA

Dependencies:
- React + Recharts + Zustand/Redux
- GraphQL/Apollo or REST clients
- Export library (html2canvas + jsPDF)
- WebSocket service for live updates

Risks & Mitigations:
- Data skew: Normalize across modules
- Export failures: Retry + user feedback
- Performance: Virtualized lists + memoization
```

### **Story 22: Admin Panel & Reporting Interface**

```
Technical Story: Admin Console & Reporting Suite for Operations
Module: Platform - Admin Ops
Developer: Full Stack Engineer
Estimated Time: 2 days

Technical Requirements:
- Build secure admin interface for monitoring users, assessments, and QC flags
- Implement real-time dashboards showing KPIs and system health
- Provide CSV/PDF export for reports and audit logs
- Support role-based access control and activity logging
- Offer bulk actions (reset assessments, push notifications)

Implementation Details:
Admin Dashboard Layout:
```tsx
const AdminConsole: React.FC = () => {
  const { data } = useQuery(ADMIN_METRICS_QUERY);
  return (
    <div className="admin-console">
      <MetricsCards metrics={data.metrics} />
      <ActivityLog entries={data.auditLogs} />
      <BulkActionsPanel />
    </div>
  );
};
```

Reporting API (Python/FastAPI):
```python
@router.get('/reports/kpi')
def export_kpi(format: str = 'csv') -> StreamingResponse:
    df = metrics_service.build_kpi_dataframe()
    if format == 'csv':
        return StreamingResponse(io.StringIO(df.to_csv(index=False)), media_type='text/csv')
    return StreamingResponse(io.BytesIO(pdf_renderer.render(df)), media_type='application/pdf')
```

Dependencies:
- Role-based auth middleware
- Time-series DB for metrics (InfluxDB/Timescale)
- Export utilities (Pandas, jsPDF)

Acceptance Criteria:
- Admins can view KPIs, pending assessments, and take bulk actions securely

Testing Strategy:
- Unit tests: API and RBAC policies
- Integration tests: Dashboards + exports
- Security tests: Permission gating

Risks & Mitigations:
- Overexposed data: Strict RBAC and logging
- Export performance: Streamed responses
```

### **Story 23: Final Validation & QA**

```
Technical Story: Final Validation, QA & Compliance Sweep
Module: Platform - Quality Assurance
Developer: QA Engineer / SRE
Estimated Time: 2 days

Technical Requirements:
- Execute end-to-end regression tests across Knowledge, Abilities, Skills
- Validate data privacy, consent, and logging compliance
- Run accessibility and localization audits
- Automate smoke tests for pipelines and deploy checks
- Document QA sign-off and release notes

Implementation Details:
QA Automation Plan:
```yaml
regression:
  scripts:
    - npm run test:integration
    - pytest tests/e2e
accessibility:
  tool: axe-core
  reports: artifacts/axe-report.json
localization:
  verify: translations/strings.json
  languages: fr,en
```

Compliance Checklist:
```python
for component in ['knowledge', 'abilities', 'skills']:
    compliance.assert_consent(component)
    compliance.assert_data_retention(component)
    compliance.assert_logging(component)
```

Acceptance Criteria:
- QA dashboard shows all systems green and compliance checks passing

Testing Strategy:
- System regression + smoke tests
- Accessibility & localization scans
- Compliance assertions + audit trail

Risks & Mitigations:
- Last-minute bugs: Freeze scope + hotfix process
- Compliance gaps: Pair with legal review
```

### **Story 24: Optimisation & Performance Tuning**

```
Technical Story: System Optimisation, Caching & Performance Tuning
Module: Platform - Performance
Developer: Backend/ML Engineer
Estimated Time: 2 days

Technical Requirements:
- Profile slow endpoints (NLP, fusion, dashboard)
- Introduce caching layer (Redis) for heavy computations
- Optimize database queries and add indexes
- Monitor latency with tracing (OpenTelemetry)
- Document SLAs and automated alerts

Implementation Details:
Optimization Script:
```python
with tracer.start_as_current_span('optimize-sql'):
    with connection.cursor() as cur:
        cur.execute('EXPLAIN ANALYZE SELECT ...')
        log.info(cur.fetchall())

cache_keys = ['profile:{}:mapping', 'dashboard:metrics']
for key in cache_keys:
    redis_cache.prewarm(key)
```

Monitoring:
```yaml
tempo:
  traces:
    - service: kash-backend
alerting:
  - name: high-latency
    condition: avg(latency) > 500ms
    action: notify(#ops)
```

Acceptance Criteria:
- Key flows under 300ms latency + cache hit rate >80%

Testing Strategy:
- Load tests + tracing dashboards
- SQL explain plans + histogram analysis
- Alerting simulation

Risks & Mitigations:
- Cache invalidation: Versioned keys + TTL
- Index bloat: Monitor index usage
```

### **Story 25: Pilot Deployment 2 Schools**

```
Technical Story: Pilot Deployment for Two Partner Schools
Module: Deployment - Pilot
Developer: DevOps / Delivery Lead
Estimated Time: 3 days

Technical Requirements:
- Provision environments for two school pilots (staging + prod)
- Configure onboarding flows, training materials, and analytics tracking
- Implement feedback collection loops (forms, session logs)
- Harden monitoring + incident playbooks
- Coordinate cutover and rollback plans

Implementation Details:
Pilot Checklist:
```text
1. Provision environments (VPC, DB, CDN)
2. Deploy app + migrations
3. Enable SSO + RBAC for schools
4. Publish onboarding guide + training site
5. Activate monitoring + feedback forms
```

Feedback Pipeline:
```python
def publish_feedback(event):
    feedback_repo.save(event)
    notify_team('pilot-feedback', event)
```

Acceptance Criteria:
- Two schools onboarded, analytics flowing, feedback channel active

Testing Strategy:
- Deployment smoke tests
- Feedback ingestion verification
- Incident drills

Risks & Mitigations:
- School-specific issues: Dedicated support rotation
- Rollback: Database snapshots + blue-green deploy
```

## Development Story Summary

| Story | Module | Developer | Time | Dependencies |
|-------|--------|-----------|------|-------------|
| Repository Setup | Infrastructure | Full Stack DevOps | 2 days | Git provider, Node.js, Python |
| CI/CD Pipeline | DevOps | DevOps Engineer | 3 days | GitHub Actions, Cloud provider |
| Cloud Infrastructure | Cloud | Cloud Architect | 3 days | Terraform, AWS/GCP/Azure |
| Database Schema | Database | Backend Engineer | 2 days | PostgreSQL, Migration tool |
| Dev Environment | Development | Full Stack | 2 days | Docker, Docker Compose |
| NLP CV Analysis | Knowledge - NLP | ML/NLP Engineer | 3 days | spaCy, Transformers, ESCO |
| ESCO Integration | Knowledge - API | Backend Integration | 2 days | ESCO/O*NET APIs, Redis |
| Adaptive Quiz | Knowledge - Quiz | Backend/ML Engineer | 3 days | IRT models, PostgreSQL |
| Knowledge Scoring | Knowledge - Scoring | Backend/ML Engineer | 2 days | NumPy, PostgreSQL |
| Frontend Interface | Knowledge - UI | Frontend Engineer | 2 days | React, Recharts, Redux |
| Text Cognitive Tests | Abilities - Text | Backend/ML Engineer | 3 days | NumPy, NLTK, PostgreSQL |
| Voice Recording | Abilities - Voice | Frontend Engineer | 2 days | Web Audio API, React |
| Speech-to-Text | Abilities - STT | ML/Backend Engineer | 3 days | Whisper API, librosa |
| Multimodal Fusion | Abilities - Fusion | ML/Backend Engineer | 3 days | NumPy, Scikit-learn |
| Mini-Projects Eval | Skills - Projects | Backend/ML Engineer | 3 days | Docker, Test frameworks |
| GitHub Integration | Skills - GitHub | Backend Integration | 2 days | GitHub API, Redis |
| Code Analysis | Skills - Analysis | ML/Backend Engineer | 3 days | AST parsers, Quality tools |
| Mapping KASH-Métiers | Skills - Mapping | Backend/AI Engineer | 3 days | Embeddings, ESCO/ROME |
| Prediction & Success Model | Skills - Prediction | Data Scientist | 3 days | XGBoost, Shap, Historical data |
| IA Explicable Layer | Platform - Explainability | ML/DevOps Engineer | 3 days | FastAPI, Postgres, Template engine |
| Dashboard 4D Integration | Frontend - Dashboard | Frontend Engineer | 2 days | React, Recharts, WebSockets |
| Admin Panel & Reporting Interface | Platform - Admin Ops | Full Stack Engineer | 2 days | RBAC, Timescale, Export utils |
| Final Validation & QA | Platform - Quality Assurance | QA/SRE | 2 days | Axe, pytest, Compliance asserts |
| Optimisation & Performance Tuning | Platform - Performance | Backend/ML Engineer | 2 days | Redis, OpenTelemetry |
| Pilot Deployment 2 Schools | Deployment - Pilot | DevOps/Delivery | 3 days | Terraform, Monitoring, Feedback hooks |

**Total Estimated Time: 64 days (Sprint 0-12)**

## Usage

Run `/dev-story --interactive` to create new technical development stories or modify existing ones.
