from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

TOTAL_STUDENTS = 64
STUDENT_FILE = "students.xlsx"

# Load student list once
df = pd.read_excel(STUDENT_FILE)
df.columns = df.columns.str.strip()

roll_col = df.columns[0]
name_col = df.columns[1]
roll_to_name = dict(zip(df[roll_col], df[name_col]))


@app.route("/attendance", methods=["POST"])
def attendance():
    data = request.json

    date = data.get("date")
    hour = data.get("hour")
    absent = data.get("absent", "")
    od = data.get("od", "")

    if not date or not hour:
        return jsonify({"error": "Date and Hour are required"}), 400

    absent_rolls = sorted(set(
        int(x) for x in absent.split(",") if x.strip().isdigit()
    ))
    od_rolls = sorted(set(
        int(x) for x in od.split(",") if x.strip().isdigit()
    ))

    # Check overlap
    common = set(absent_rolls) & set(od_rolls)
    if common:
        return jsonify({
            "warning": f"Roll numbers present in BOTH Absentees and OD: {', '.join(map(str, common))}"
        })

    present = TOTAL_STUDENTS - len(absent_rolls)
    percentage = round((present / TOTAL_STUDENTS) * 100)

    absentees = [
        f"{roll_to_name[r]} ({r})"
        for r in absent_rolls if r in roll_to_name
    ]

    ods = [
        f"{roll_to_name[r]} ({r})"
        for r in od_rolls if r in roll_to_name
    ]

    result = f"""Good morning sir,
Date : {date}
Hour: {hour}
II YEAR - A
B.Tech IT  : {present}/64
--------------------------------
Percentage : {percentage}%

 *Absentees List
"""

    for i, a in enumerate(absentees, 1):
        result += f"{i}. {a}\n"

    result += "\nOD\n"
    for i, o in enumerate(ods, 1):
        result += f"{i}. {o}\n"

    result += "\nThank you sir"

    return jsonify({"output": result})


if __name__ == "__main__":
    app.run()
