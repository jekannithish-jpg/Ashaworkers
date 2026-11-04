import os
import glob
import json
import re
import math
from typing import List, Dict, Any, Tuple

class MaternalHealthRAGAssistant:
    def __init__(self, kb_dir: str):
        self.kb_dir = kb_dir
        self.documents: List[Dict[str, Any]] = []
        self.passages: List[Dict[str, Any]] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        json_files = glob.glob(os.path.join(self.kb_dir, "*.json"))
        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    docs = json.load(f)
                    for doc in docs:
                        self.documents.append(doc)
                        doc_code = doc.get("document_code", "UNKNOWN")
                        doc_title = doc.get("title", "Government Guidelines")
                        doc_org = doc.get("organization", "MoHFW/NHM")
                        doc_ver = doc.get("version", "1.0.0")

                        for sec in doc.get("sections", []):
                            self.passages.append({
                                "document_code": doc_code,
                                "document_title": doc_title,
                                "organization": doc_org,
                                "version": doc_ver,
                                "section_id": sec.get("section_id"),
                                "topic": sec.get("topic"),
                                "keywords": sec.get("keywords", []),
                                "content": sec.get("content", "")
                            })
            except Exception as e:
                print(f"Error loading knowledge file {fpath}: {e}")

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\u0B80-\u0BFF]+\b", text.lower())
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "are", "what", "which", "how", "does"}
        return [w for w in words if w not in stop_words and len(w) > 1]

    def _calculate_score(self, query_tokens: List[str], passage: Dict[str, Any]) -> float:
        score = 0.0
        passage_text = (passage["topic"] + " " + " ".join(passage["keywords"]) + " " + passage["content"]).lower()
        topic_text = passage["topic"].lower()
        keywords_text = " ".join(passage["keywords"]).lower()

        for token in query_tokens:
            if token in topic_text:
                score += 5.0
            if token in keywords_text:
                score += 4.0
            if token in passage_text:
                count = passage_text.count(token)
                score += 1.0 + math.log(1 + count)

        return score

    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Processes query with strict clinical guardrails and retrieval from approved MoHFW/NHM documents.
        """
        clean_q = query.strip()
        query_lower = clean_q.lower()

        # Guardrail 1: Clinical Diagnosis or Medicine Prescription Request
        diagnosis_rx_keywords = ["prescribe", "dosage for me", "what medicine should i take", "diagnose my", "am i having pre-eclampsia", "give me antibiotic"]
        if any(kw in query_lower for kw in diagnosis_rx_keywords):
            return {
                "answer": "CLINICAL SAFETY ALERT: As an approved information assistant for health workers, I cannot provide individualized clinical diagnoses, prescribe medications, or replace direct doctor assessments. If the beneficiary shows acute symptoms or severe pain, immediately arrange an emergency referral to a qualified Medical Officer or dial 108 Emergency Ambulance.",
                "sources": [],
                "confidence": 1.0,
                "is_out_of_scope": True,
                "requires_urgent_action": True
            }

        # Guardrail 2: Retrieval Matching
        query_tokens = self._tokenize(clean_q)
        if not query_tokens:
            return {
                "answer": "Please ask a specific question regarding approved maternal health protocols, such as ANC schedules, danger signs, IFA supplementation, or home visit checklists.",
                "sources": [],
                "confidence": 0.0,
                "is_out_of_scope": False
            }

        scored_passages = []
        for p in self.passages:
            score = self._calculate_score(query_tokens, p)
            if score > 0:
                scored_passages.append((score, p))

        scored_passages.sort(key=lambda x: x[0], reverse=True)

        if not scored_passages or scored_passages[0][0] < 2.5:
            return {
                "answer": f"Information regarding '{clean_q}' was not found in the approved MoHFW/NHM maternal health knowledge base. For questions outside approved guidelines, please consult your Primary Health Centre Medical Officer or reference official NHM training manuals.",
                "sources": [],
                "confidence": 0.0,
                "is_out_of_scope": True
            }

        top_passage = scored_passages[0][1]
        top_score = scored_passages[0][0]

        sources = [
            {
                "document_title": top_passage["document_title"],
                "organization": top_passage["organization"],
                "version": top_passage["version"],
                "document_code": top_passage["document_code"],
                "topic": top_passage["topic"]
            }
        ]

        # Synthesize clear, concise answer from approved passage
        answer_text = f"**{top_passage['topic']}**\n\n{top_passage['content']}\n\n*Note: This response is retrieved verbatim from approved government maternal health documentation. Always follow standard field protocols.*"

        return {
            "answer": answer_text,
            "sources": sources,
            "confidence": min(1.0, top_score / 10.0),
            "is_out_of_scope": False
        }

# Global assistant singleton
_kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base")
rag_assistant = MaternalHealthRAGAssistant(_kb_dir)

