#!/usr/bin/env python3
"""
HILDE Suffix Preservation Service
Handles regeneration of code suffixes when tokens are replaced
"""

import re
import ast
from typing import List, Tuple, Optional
from difflib import SequenceMatcher

class SuffixPreservationService:
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def regenerate_suffix(self, original_code: str, new_token: str, position: int, 
                         completion_engine) -> str:
        """
        Regenerate code suffix after token replacement
        
        Args:
            original_code: The original complete code
            new_token: The new token that was selected
            position: Position where the token was replaced
            completion_engine: The completion LLM engine
            
        Returns:
            Regenerated suffix that best preserves the original intent
        """
        try:
            # Generate multiple candidate suffixes
            candidates = self._generate_candidate_suffixes(
                original_code, new_token, position, completion_engine
            )
            
            # Find the best candidate based on similarity to original
            best_candidate = self._select_best_suffix(
                candidates, original_code, position
            )
            
            return best_candidate
            
        except Exception as e:
            print(f"Suffix regeneration failed: {e}")
            # Return original suffix as fallback
            return original_code[position + len(new_token):]
    
    def _generate_candidate_suffixes(self, original_code: str, new_token: str, 
                                   position: int, completion_engine) -> List[str]:
        """Generate multiple candidate suffixes"""
        candidates = []
        
        # Get the context before the replacement
        context = original_code[:position]
        
        # Generate 10 different completions
        for i in range(10):
            try:
                # Adjust temperature for diversity
                temperature = 0.1 + (i * 0.1)
                
                # Generate completion from the new token
                prompt = context + new_token
                completion = completion_engine.generate_completion(
                    prompt, max_tokens=100, temperature=temperature
                )
                
                # Extract the suffix (everything after the new token)
                if completion.startswith(prompt):
                    suffix = completion[len(prompt):]
                    candidates.append(suffix)
                else:
                    # Fallback: use the completion as suffix
                    candidates.append(completion)
                    
            except Exception as e:
                print(f"Candidate {i} generation failed: {e}")
                continue
        
        return candidates
    
    def _select_best_suffix(self, candidates: List[str], original_code: str, 
                           position: int) -> str:
        """Select the best suffix based on similarity to original"""
        if not candidates:
            return ""
        
        original_suffix = original_code[position:]
        best_candidate = candidates[0]
        best_similarity = 0.0
        
        for candidate in candidates:
            # Calculate similarity using multiple metrics
            similarity = self._calculate_similarity(candidate, original_suffix)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_candidate = candidate
        
        # Only use candidate if similarity is above threshold
        if best_similarity >= self.similarity_threshold:
            return best_candidate
        else:
            # Return original suffix if no good candidate found
            return original_suffix
    
    def _calculate_similarity(self, candidate: str, original: str) -> float:
        """Calculate similarity between candidate and original suffix"""
        if not candidate or not original:
            return 0.0
        
        # Use SequenceMatcher for string similarity
        matcher = SequenceMatcher(None, candidate, original)
        string_similarity = matcher.ratio()
        
        # Try to parse as AST for structural similarity
        ast_similarity = self._calculate_ast_similarity(candidate, original)
        
        # Combine similarities (weighted average)
        combined_similarity = (string_similarity * 0.7) + (ast_similarity * 0.3)
        
        return combined_similarity
    
    def _calculate_ast_similarity(self, candidate: str, original: str) -> float:
        """Calculate AST-based similarity"""
        try:
            candidate_ast = ast.parse(candidate)
            original_ast = ast.parse(original)
            
            # Simple AST node count comparison
            candidate_nodes = self._count_ast_nodes(candidate_ast)
            original_nodes = self._count_ast_nodes(original_ast)
            
            if original_nodes == 0:
                return 0.0
            
            # Calculate similarity based on node count ratio
            ratio = min(candidate_nodes, original_nodes) / max(candidate_nodes, original_nodes)
            return ratio
            
        except SyntaxError:
            # If parsing fails, return low similarity
            return 0.1
    
    def _count_ast_nodes(self, ast_tree) -> int:
        """Count AST nodes recursively"""
        count = 1
        for child in ast.iter_child_nodes(ast_tree):
            count += self._count_ast_nodes(child)
        return count

# Example usage
if __name__ == "__main__":
    service = SuffixPreservationService()
    
    # Test with sample code
    original_code = "def calculate_hash(password):\n    return hashlib.sha256(password.encode()).hexdigest()"
    new_token = "scrypt"
    position = 25  # Position of "sha256"
    
    # This would be called with a real completion engine
    print("Suffix preservation service initialized")
