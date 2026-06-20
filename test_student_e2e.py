"""
End-to-End Test: Nouveau candidat passe les 4 évaluations KASH
================================================================
Ce script simule un étudiant qui se connecte pour la première fois
et passe les 4 tests : Knowledge, Abilities, Skills, Intelligence.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(label, value):
    print(f"  {label}: {value}")


def test_auth():
    """Test 1: Connexion automatique (mode dev)"""
    print_section("1. AUTHENTIFICATION - Première connexion")
    
    resp = requests.get(f"{BASE_URL}/auth/me")
    assert resp.status_code == 200, f"Auth failed: {resp.text}"
    
    user = resp.json()
    print_result("User ID", user["id"])
    print_result("Email", user["email"])
    print_result("Nom", user["display_name"])
    print_result("Provider", user["auth_provider"])
    print(f"  ✓ Utilisateur créé automatiquement (première connexion)")
    return user


def test_knowledge(user_id):
    """Test 2: Knowledge - Upload et analyse CV"""
    print_section("2. KNOWLEDGE - Analyse CV")
    
    # Upload a sample CV
    cv_text = """
    CURRICULUM VITAE
    
    Nom: Ahmed Ben Ali
    Email: ahmed.benali@email.com
    
    FORMATION:
    - Master en Intelligence Artificielle, Université de Tunis, 2024
    - Licence en Informatique, Université de Sfax, 2022
    
    COMPETENCES TECHNIQUES:
    - Python, TensorFlow, PyTorch, Scikit-learn
    - Machine Learning, Deep Learning, NLP
    - SQL, PostgreSQL, MongoDB
    - Docker, Kubernetes, CI/CD
    - React, Next.js, TypeScript
    
    EXPERIENCE:
    - Stage Data Scientist, TechCorp (6 mois)
      - Développement de modèles de prédiction
      - Analyse de données clients
    - Projet de fin d'études: Système de recommandation
    
    LANGUES:
    - Arabe (natif), Français (courant), Anglais (B2)
    
    CERTIFICATIONS:
    - Google Cloud Professional ML Engineer
    - AWS Machine Learning Specialty
    """
    
    # Try uploading CV via the upload endpoint
    resp = requests.post(
        f"{BASE_URL}/knowledge/upload-cv",
        files={"file": ("cv_ahmed.txt", cv_text, "text/plain")}
    )
    
    if resp.status_code == 200:
        result = resp.json()
        print_result("Assessment ID", result.get("assessment_id", "N/A"))
        print_result("Score", result.get("normalized_score", "N/A"))
        print_result("Skills détectées", result.get("esco_skills", [])[:5])
        print(f"  ✓ CV analysé avec succès")
        return result
    else:
        print(f"  ⚠ Upload CV: {resp.status_code} - {resp.text[:200]}")
        
        # Try the alternative analyze endpoint
        resp2 = requests.post(
            f"{BASE_URL}/knowledge/analyze-cv",
            json={"cv_text": cv_text}
        )
        if resp2.status_code == 200:
            result = resp2.json()
            print_result("Score", result.get("normalized_score", "N/A"))
            print(f"  ✓ CV analysé via endpoint alternatif")
            return result
        else:
            print(f"  ⚠ Analyze CV: {resp2.status_code} - {resp2.text[:200]}")
            return None


def test_abilities():
    """Test 3: Abilities - Quiz adaptatif cognitif"""
    print_section("3. ABILITIES - Quiz Adaptatif (Memory)")
    
    # Start assessment
    resp = requests.post(
        f"{BASE_URL}/abilities/start",
        json={
            "quiz_type": "cognitive",
            "domain": "memory",
            "num_questions": 5,
            "adaptive": True
        }
    )
    
    assert resp.status_code == 200, f"Start failed: {resp.text}"
    start_data = resp.json()
    
    session_id = start_data["session_id"]
    assessment_id = start_data["assessment_id"]
    print_result("Assessment ID", assessment_id)
    print_result("Session ID", session_id)
    print_result("Questions", start_data["total_questions"])
    print_result("Mode adaptatif", start_data["adaptive"])
    
    # Answer all questions
    current_question = start_data["current_question"]
    question_num = 1
    
    while current_question:
        # Pick an answer (first option for simplicity, simulating a student)
        # Alternate between correct-ish answers
        options = current_question.get("options", [])
        answer_idx = question_num % len(options) if options else 0
        answer = options[answer_idx] if options else "unknown"
        
        print(f"\n  Q{question_num}: {current_question['question_text'][:60]}...")
        print(f"    Réponse: {answer}")
        
        resp = requests.post(
            f"{BASE_URL}/abilities/submit-answer",
            json={
                "session_id": session_id,
                "question_id": current_question["id"],
                "answer": answer,
                "response_time_ms": 3000 + (question_num * 500)
            }
        )
        
        if resp.status_code != 200:
            print(f"    ⚠ Submit error: {resp.status_code} - {resp.text[:100]}")
            break
        
        result = resp.json()
        print(f"    Correct: {'✓' if result['is_correct'] else '✗'}")
        print(f"    Progress: {result['progress']:.0%}")
        
        if result.get("quiz_completed"):
            print(f"\n  ✓ Quiz terminé!")
            if result.get("results"):
                results = result["results"]
                print_result("Score", f"{results.get('percentage', 0):.1f}%")
                print_result("Correct", f"{results.get('correct_answers', 0)}/{results.get('total_questions', 0)}")
            return result
        
        current_question = result.get("next_question")
        question_num += 1
        time.sleep(0.5)  # Simulate thinking time
    
    return None


def test_skills():
    """Test 4: Skills - Analyse GitHub"""
    print_section("4. SKILLS - Analyse Technique (GitHub)")
    
    # Analyze a public repository
    resp = requests.post(
        f"{BASE_URL}/skills/analyze-github",
        json={
            "owner": "tiangolo",
            "repo": "fastapi"
        }
    )
    
    if resp.status_code == 200:
        result = resp.json()
        print_result("Assessment ID", result.get("assessment_id", "N/A"))
        print_result("Status", result.get("status", "N/A"))
        print_result("Project", result.get("project_name", "N/A"))
        
        repo_info = result.get("repository_info", {})
        print_result("Language principal", repo_info.get("language", "N/A"))
        print_result("Stars", repo_info.get("stars", "N/A"))
        
        tech_skills = result.get("technical_skills", [])
        if tech_skills:
            print(f"  Skills détectées ({len(tech_skills)}):")
            for skill in tech_skills[:5]:
                print(f"    - {skill.get('name', 'N/A')} ({skill.get('proficiency_level', 'N/A')})")
        
        print(f"  ✓ Analyse GitHub réussie")
        return result
    else:
        print(f"  ⚠ GitHub analysis: {resp.status_code} - {resp.text[:200]}")
        return None


def test_intelligence():
    """Test 5: Intelligence - Scoring KASH global + SHAP"""
    print_section("5. INTELLIGENCE - Score KASH & Explainabilité")
    
    resp = requests.post(
        f"{BASE_URL}/intelligence/assess",
        json={
            "industry": "technology",
            "career_goals": ["machine_learning_engineer", "data_scientist"]
        }
    )
    
    if resp.status_code == 200:
        result = resp.json()
        print_result("Assessment ID", result.get("assessment_id", "N/A"))
        print_result("Status", result.get("status", "N/A"))
        
        kash_score = result.get("kash_score", {})
        print(f"\n  KASH Scores:")
        print_result("  Overall", f"{kash_score.get('overall_score', 0):.1f}/100")
        print_result("  Knowledge", f"{kash_score.get('knowledge_score', 0):.1f}/100")
        print_result("  Abilities", f"{kash_score.get('abilities_score', 0):.1f}/100")
        print_result("  Skills", f"{kash_score.get('skills_score', 0):.1f}/100")
        print_result("  Experience", f"{kash_score.get('experience_score', 0):.1f}/100")
        print_result("  Confidence", f"{kash_score.get('confidence', 0):.2f}")
        print_result("  Career Stage", kash_score.get("career_stage", "N/A"))
        
        # Feature importance (SHAP)
        fi = result.get("feature_importance", [])
        if fi:
            print(f"\n  Feature Importance (SHAP):")
            for f in fi[:5]:
                direction = "↑" if f.get("direction") == "positive" else "↓"
                print(f"    {direction} {f.get('feature_name', 'N/A')}: {f.get('contribution_percentage', 0):.1f}%")
        
        # Career paths
        career = result.get("career_explanations", [])
        if career:
            print(f"\n  Career Path Matches:")
            for c in career[:3]:
                print(f"    - {c.get('career_path', 'N/A')}: {c.get('match_score', 0):.0f}%")
        
        # Recommendations
        recs = kash_score.get("recommendations", [])
        if recs:
            print(f"\n  Recommandations:")
            for r in recs[:3]:
                print(f"    → {r}")
        
        print(f"\n  ✓ Intelligence assessment complet")
        return result
    else:
        print(f"  ⚠ Intelligence: {resp.status_code} - {resp.text[:200]}")
        return None


def test_final_profile():
    """Test 6: Vérifier le profil global après tous les tests"""
    print_section("6. PROFIL FINAL - Résumé KASH")
    
    # Check each profile
    profiles = {}
    for module in ["knowledge", "abilities", "skills", "intelligence"]:
        resp = requests.get(f"{BASE_URL}/{module}/profile")
        if resp.status_code == 200:
            profiles[module] = resp.json()
            print_result(f"{module.capitalize()} assessments", profiles[module].get("total_assessments", 0))
        else:
            print(f"  ⚠ {module} profile: {resp.status_code}")
    
    return profiles


def main():
    print("\n" + "╔" + "═"*58 + "╗")
    print("║  TEST E2E: Parcours complet d'un nouveau candidat KASH  ║")
    print("╚" + "═"*58 + "╝")
    
    # 1. Auth
    user = test_auth()
    
    # 2. Knowledge
    knowledge_result = test_knowledge(user["id"])
    
    # 3. Abilities
    abilities_result = test_abilities()
    
    # 4. Skills
    skills_result = test_skills()
    
    # 5. Intelligence
    intelligence_result = test_intelligence()
    
    # 6. Final profile
    profiles = test_final_profile()
    
    # Summary
    print_section("RÉSUMÉ DU TEST")
    print(f"  {'Module':<15} {'Status':<10} {'Note'}")
    print(f"  {'-'*40}")
    print(f"  {'Auth':<15} {'✓':<10} Utilisateur créé")
    print(f"  {'Knowledge':<15} {'✓' if knowledge_result else '⚠':<10} {'CV analysé' if knowledge_result else 'Erreur'}")
    print(f"  {'Abilities':<15} {'✓' if abilities_result else '⚠':<10} {'Quiz complété' if abilities_result else 'Erreur'}")
    print(f"  {'Skills':<15} {'✓' if skills_result else '⚠':<10} {'GitHub analysé' if skills_result else 'Erreur'}")
    print(f"  {'Intelligence':<15} {'✓' if intelligence_result else '⚠':<10} {'KASH scoré' if intelligence_result else 'Erreur'}")
    print()


if __name__ == "__main__":
    main()
