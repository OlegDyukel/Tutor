import data
import json

lst_data = [data.goals, data.teachers]

with open("data.json", 'w') as f:
    json.dump(lst_data, f)

