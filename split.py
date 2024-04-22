import json

with open('combinations.json', 'r') as f:
    data = json.load(f)
    total_length = len(data)
    split_index_1 = total_length // 3
    split_index_2 = 2 * total_length // 3

    first_part = data[:split_index_1]
    second_part = data[split_index_1:split_index_2]
    third_part = data[split_index_2:]

    with open('combination_1.json', 'w') as f:
        json.dump(first_part, f, indent=2, default=str)
        
    with open('combination_2.json', 'w') as f:
        json.dump(second_part, f, indent=2, default=str)

    with open('combination_3.json', 'w') as f:
        json.dump(third_part, f, indent=2, default=str)
