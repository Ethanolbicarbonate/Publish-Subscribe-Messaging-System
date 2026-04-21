"""
Topic Manager for the Broker.
Handles subscription mappings, thread-safe modifications, and
wildcard topic matching (e.g., 'STOCK.*' matches 'STOCK.AAPL').
"""

import threading
from typing import Set, Dict

class TopicManager:
    def __init__(self):
        # Maps a topic pattern (e.g., 'STOCK.*') to a set of subscriber_ids
        self._pattern_to_subs: Dict[str, Set[str]] = {}
        # Maps a subscriber_id to a set of topic patterns they are subscribed to
        self._sub_to_patterns: Dict[str, Set[str]] = {}
        
        # Re-entrant lock for thread-safe operations across client threads
        self._lock = threading.RLock()

    def add_subscription(self, subscriber_id: str, topic_pattern: str) -> None:
        """Adds a subscriber to a specific topic pattern."""
        with self._lock:
            # Update pattern -> subscribers map
            if topic_pattern not in self._pattern_to_subs:
                self._pattern_to_subs[topic_pattern] = set()
            self._pattern_to_subs[topic_pattern].add(subscriber_id)

            # Update subscriber -> patterns map
            if subscriber_id not in self._sub_to_patterns:
                self._sub_to_patterns[subscriber_id] = set()
            self._sub_to_patterns[subscriber_id].add(topic_pattern)
            
            print(f"[TopicManager] Subscriber {subscriber_id} subscribed to '{topic_pattern}'")

    def remove_subscription(self, subscriber_id: str, topic_pattern: str) -> None:
        """Removes a specific topic pattern subscription for a subscriber."""
        with self._lock:
            # Remove from pattern -> subscribers map
            if topic_pattern in self._pattern_to_subs:
                self._pattern_to_subs[topic_pattern].discard(subscriber_id)
                # Cleanup empty sets to save memory
                if not self._pattern_to_subs[topic_pattern]:
                    del self._pattern_to_subs[topic_pattern]

            # Remove from subscriber -> patterns map
            if subscriber_id in self._sub_to_patterns:
                self._sub_to_patterns[subscriber_id].discard(topic_pattern)
                if not self._sub_to_patterns[subscriber_id]:
                    del self._sub_to_patterns[subscriber_id]
                    
            print(f"[TopicManager] Subscriber {subscriber_id} unsubscribed from '{topic_pattern}'")

    def remove_all_subscriptions(self, subscriber_id: str) -> None:
        """Clears all subscriptions for a given subscriber (e.g., on disconnect)."""
        with self._lock:
            # Take a copy of the set to safely iterate while modifying the original structures
            patterns = self._sub_to_patterns.get(subscriber_id, set()).copy()
            for pattern in patterns:
                self.remove_subscription(subscriber_id, pattern)

    def get_subscribers(self, published_topic: str) -> Set[str]:
        """
        Finds all subscriber IDs that should receive a message published to `published_topic`.
        Supports exact matches and single-level wildcards (e.g., 'STOCK.*').
        """
        matched_subs = set()
        with self._lock:
            for pattern, subs in self._pattern_to_subs.items():
                if self._matches(pattern, published_topic):
                    matched_subs.update(subs)
        return matched_subs

    def _matches(self, pattern: str, topic: str) -> bool:
        """
        Checks if a published topic matches a subscription pattern.
        Rules:
        - Exact string match returns True
        - Segment-by-segment match where '*' acts as a wildcard for a single segment
          Example: 'STOCK.*' matches 'STOCK.AAPL' but NOT 'STOCK.AAPL.OPTIONS'
        """
        if pattern == topic:
            return True
            
        pattern_segments = pattern.split('.')
        topic_segments = topic.split('.')
        
        # For our basic wildcard rule, segment count must be identical
        if len(pattern_segments) != len(topic_segments):
            return False
            
        for p_seg, t_seg in zip(pattern_segments, topic_segments):
            if p_seg != '*' and p_seg != t_seg:
                return False
                
        return True