from router import ModelRouter

r = ModelRouter()

test_cases = [
    ("write a python function to sort a list", "Coding task"),
    ("what is the capital of France?", "General Q&A"),
    ("explain quantum mechanics", "Reasoning task"),
    ("fix this bug: TypeError undefined", "Debugging"),
    ("write a story about a dragon", "Writing"),
    ("hello how are you", "General chat"),
]

print("🧪 Testing Advanced Model Router\n")
print("=" * 70)

for prompt, description in test_cases:
    selected = r.route(prompt)
    reasoning = r.get_routing_reasoning(prompt)
    scores = r.get_all_scores(prompt)
    
    print(f"\n📝 {description}: \"{prompt}\"")
    print(f"   → Selected: {selected}")
    print(f"   → Reason: {reasoning}")
    print(f"   → Scores: qwen2.5-coder={scores['qwen2.5-coder:7b']:.2f}, qwen4b={scores['qwen:4b']:.2f}")
    print("-" * 70)

print("\n✅ All tests completed!")
