# HCSP Toolkit
# Author: Daniel Ervilha
# Type: lib
ABOUT = """
"""
import os
import re

# File management
def lookup(directory: str, key: str, recursive_search: bool = True, use_regex: bool = False) -> list[str]:
    """
        Searches for matches to a given key in the specified directory.

        ## Keys:
            `+`: Any single character
            `*`: Any number of characters
            `#`: Any single numberic character
            `&`: Any alphabetic character

        ## Parameters:
            directory (str): Path to the directory to search in.
            key (str): The term or pattern to search for.
            recursive_search (bool): Whether to search in subdirectories. Default: True.
            use_regex (bool): Whether the key should be treated as a regular expression. Default: False.

        ## Returns:
            list[str]: A list of paths or matches found in the directory.
    """
    pattern = re.compile(key) if use_regex else re.compile((
        key
        .replace('+', r'.')
        .replace('*', r'.*')
        .replace('#', r'\d')
        .replace('&', r'\w')
    ))

    matches = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            if recursive_search:
                matches.extend(lookup(item_path, key, recursive_search, use_regex))
            continue
        
        if pattern.match(item):
            matches.append(item_path)
    
    return matches
