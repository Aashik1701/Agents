#!/usr/bin/env python3
"""
Advanced Multi-Collection Search Engine
Handles partial matches, typos, and fuzzy searching across all FAQ collections
"""

import re
import difflib
from collections import defaultdict
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI, MONGODB_DATABASE, USE_ATLAS, LOCAL_MONGODB_URI

class AdvancedFAQSearcher:
    def __init__(self):
        """Initialize the search engine with multiple collections"""
        self.client = self.get_client()
        self.db = self.client[MONGODB_DATABASE]
        
        # Define all FAQ collections
        self.collection_names = [
            "general_faqs",
            "technology_faqs", 
            "business_faqs",
            "science_faqs",
            "health_faqs"
        ]
        
        # Load all questions into memory for fuzzy matching
        self.all_questions = self.load_all_questions()
    
    def get_client(self):
        """Get MongoDB client based on configuration"""
        if USE_ATLAS:
            return MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        else:
            return MongoClient(LOCAL_MONGODB_URI)
    
    def load_all_questions(self):
        """Load all questions from all collections for fuzzy matching"""
        all_questions = {}
        
        for collection_name in self.collection_names:
            try:
                collection = self.db[collection_name]
                docs = list(collection.find({}, {"question": 1, "answer": 1}))
                
                for doc in docs:
                    question_key = f"{collection_name}:{doc['_id']}"
                    all_questions[question_key] = {
                        "question": doc["question"],
                        "answer": doc["answer"],
                        "collection": collection_name
                    }
            except Exception as e:
                print(f"Error loading {collection_name}: {e}")
        
        return all_questions
    
    def normalize_text(self, text):
        """Normalize text for better matching"""
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation except letters, numbers, and spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts using difflib"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def exact_match_search(self, user_input):
        """Method 1: Exact match across all collections"""
        normalized_input = self.normalize_text(user_input)
        
        for collection_name in self.collection_names:
            collection = self.db[collection_name]
            
            # Try exact match (case-insensitive)
            record = collection.find_one({
                "question": {"$regex": f"^{re.escape(normalized_input)}$", "$options": "i"}
            })
            
            if record:
                return {
                    "answer": record["answer"],
                    "confidence": 1.0,
                    "method": "exact_match",
                    "collection": collection_name,
                    "matched_question": record["question"]
                }
        
        return None
    
    def partial_match_search(self, user_input):
        """Method 2: Partial match using regex across all collections"""
        normalized_input = self.normalize_text(user_input)
        results = []
        
        for collection_name in self.collection_names:
            collection = self.db[collection_name]
            
            # Search for questions containing the input
            regex_pattern = re.escape(normalized_input)
            docs = list(collection.find({
                "question": {"$regex": regex_pattern, "$options": "i"}
            }))
            
            for doc in docs:
                # Calculate confidence based on how much of the question matches
                question_words = set(self.normalize_text(doc["question"]).split())
                input_words = set(normalized_input.split())
                
                if input_words:
                    confidence = len(input_words.intersection(question_words)) / len(input_words)
                    
                    results.append({
                        "answer": doc["answer"],
                        "confidence": confidence,
                        "method": "partial_match",
                        "collection": collection_name,
                        "matched_question": doc["question"]
                    })
        
        # Return best match
        if results:
            best_result = max(results, key=lambda x: x["confidence"])
            if best_result["confidence"] > 0.5:  # Minimum confidence threshold
                return best_result
        
        return None
    
    def fuzzy_match_search(self, user_input):
        """Method 3: Fuzzy matching using difflib for typos and partial text"""
        normalized_input = self.normalize_text(user_input)
        best_matches = []
        
        for question_key, question_data in self.all_questions.items():
            normalized_question = self.normalize_text(question_data["question"])
            
            # Calculate similarity ratio
            similarity = self.calculate_similarity(normalized_input, normalized_question)
            
            if similarity > 0.6:  # Minimum similarity threshold
                best_matches.append({
                    "answer": question_data["answer"],
                    "confidence": similarity,
                    "method": "fuzzy_match",
                    "collection": question_data["collection"],
                    "matched_question": question_data["question"],
                    "similarity": similarity
                })
        
        if best_matches:
            # Sort by similarity and return the best match
            best_matches.sort(key=lambda x: x["similarity"], reverse=True)
            return best_matches[0]
        
        return None
    
    def keyword_match_search(self, user_input):
        """Method 4: Keyword-based matching across all collections"""
        normalized_input = self.normalize_text(user_input)
        input_words = set(normalized_input.split())
        
        if not input_words:
            return None
        
        results = []
        
        for collection_name in self.collection_names:
            collection = self.db[collection_name]
            
            # Build regex pattern for any of the keywords
            keyword_patterns = [re.escape(word) for word in input_words if len(word) > 2]
            
            if keyword_patterns:
                pattern = "|".join(keyword_patterns)
                docs = list(collection.find({
                    "$or": [
                        {"question": {"$regex": pattern, "$options": "i"}},
                        {"answer": {"$regex": pattern, "$options": "i"}}
                    ]
                }))
                
                for doc in docs:
                    question_words = set(self.normalize_text(doc["question"]).split())
                    answer_words = set(self.normalize_text(doc["answer"]).split())
                    all_doc_words = question_words.union(answer_words)
                    
                    # Calculate keyword match ratio
                    matched_keywords = input_words.intersection(all_doc_words)
                    confidence = len(matched_keywords) / len(input_words) if input_words else 0
                    
                    if confidence > 0.3:  # Minimum keyword match threshold
                        results.append({
                            "answer": doc["answer"],
                            "confidence": confidence,
                            "method": "keyword_match",
                            "collection": collection_name,
                            "matched_question": doc["question"],
                            "matched_keywords": list(matched_keywords)
                        })
        
        if results:
            best_result = max(results, key=lambda x: x["confidence"])
            return best_result
        
        return None
    
    def text_search(self, user_input):
        """Method 5: MongoDB text search across all collections"""
        results = []
        
        for collection_name in self.collection_names:
            collection = self.db[collection_name]
            
            try:
                docs = list(collection.find({
                    "$text": {"$search": user_input}
                }, {
                    "score": {"$meta": "textScore"}
                }).sort([("score", {"$meta": "textScore"})]))
                
                for doc in docs:
                    results.append({
                        "answer": doc["answer"],
                        "confidence": doc.get("score", 0) / 10,  # Normalize score
                        "method": "text_search",
                        "collection": collection_name,
                        "matched_question": doc["question"],
                        "text_score": doc.get("score", 0)
                    })
                    
            except Exception:
                # Text index might not exist for this collection
                continue
        
        if results:
            best_result = max(results, key=lambda x: x["confidence"])
            return best_result
        
        return None
    
    def search(self, user_input):
        """
        Main search function that tries multiple methods in order of accuracy
        Returns the best match with confidence score and method used
        """
        if not user_input or not user_input.strip():
            return {
                "answer": "Please ask me a question!",
                "confidence": 0,
                "method": "no_input",
                "collection": None,
                "matched_question": None
            }
        
        # Try search methods in order of accuracy
        search_methods = [
            self.exact_match_search,
            self.partial_match_search,
            self.fuzzy_match_search,
            self.text_search,
            self.keyword_match_search
        ]
        
        for method in search_methods:
            try:
                result = method(user_input)
                if result and result.get("confidence", 0) > 0.5:
                    return result
            except Exception as e:
                print(f"Error in {method.__name__}: {e}")
                continue
        
        # If no good match found, try with lower confidence threshold
        for method in search_methods[2:]:  # Skip exact and partial match
            try:
                result = method(user_input)
                if result and result.get("confidence", 0) > 0.3:
                    result["answer"] = f"I think you might be asking about: {result['answer']}"
                    return result
            except Exception as e:
                continue
        
        # Return default response with suggestions
        return self.get_default_response()
    
    def get_default_response(self):
        """Return default response with sample questions"""
        try:
            sample_questions = []
            for collection_name in self.collection_names[:3]:  # Sample from first 3 collections
                collection = self.db[collection_name]
                sample = list(collection.find({}, {"question": 1}).limit(2))
                sample_questions.extend([doc["question"] for doc in sample])
            
            if sample_questions:
                questions_text = '", "'.join(sample_questions[:5])
                return {
                    "answer": f'I couldn\'t find a good match for your question. Try asking: "{questions_text}"',
                    "confidence": 0,
                    "method": "no_match",
                    "collection": None,
                    "matched_question": None
                }
        except Exception:
            pass
        
        return {
            "answer": "I'm sorry, I couldn't understand your question. Please try rephrasing it.",
            "confidence": 0,
            "method": "no_match",
            "collection": None,
            "matched_question": None
        }
    
    def get_stats(self):
        """Get statistics about all collections"""
        stats = {
            "total_collections": len(self.collection_names),
            "collections": {},
            "total_questions": 0
        }
        
        for collection_name in self.collection_names:
            try:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                stats["collections"][collection_name] = count
                stats["total_questions"] += count
            except Exception as e:
                stats["collections"][collection_name] = f"Error: {e}"
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Test the search engine
if __name__ == "__main__":
    searcher = AdvancedFAQSearcher()
    
    # Test queries with various error types
    test_queries = [
        "hello",                    # Exact match
        "what is mongodv",         # Typo
        "wat is python",           # Typo + abbreviation
        "tell me about flask",     # Partial match
        "artificial intel",        # Incomplete word
        "how r u",                 # Abbreviation
        "goodbye",                 # Exact match
        "wat is helth",           # Multiple typos
        "databse",                # Missing letter
        "machne learning",        # Missing letters
    ]
    
    print("🧪 Testing Advanced Search Engine")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = searcher.search(query)
        print(f"   📍 Method: {result['method']}")
        print(f"   🎯 Confidence: {result['confidence']:.2f}")
        print(f"   📁 Collection: {result['collection']}")
        print(f"   💬 Answer: {result['answer'][:100]}...")
        if result.get('matched_question'):
            print(f"   ❓ Matched: '{result['matched_question']}'")
    
    # Show stats
    print(f"\n📊 Database Statistics:")
    stats = searcher.get_stats()
    print(f"   Collections: {stats['total_collections']}")
    print(f"   Total Questions: {stats['total_questions']}")
    
    searcher.close()
