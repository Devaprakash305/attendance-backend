from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)


ATTENDANCE_FILE = "attendance.xlsx"

def load_attendance_df():
    try:
        df = pd.read_excel(ATTENDANCE_FILE)
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        # If file is empty or missing, create a new DataFrame
        columns = ["Roll No", "Name", "Total Present", "Total Classes", "Percentage"]
        return pd.DataFrame(columns=columns)

def save_attendance_df(df):
    df.to_excel(ATTENDANCE_FILE, index=False)

def get_roll_to_name(df):
    roll_col = df.columns[0]
    name_col = df.columns[1]
    return dict(zip(df[roll_col], df[name_col]))


@app.route("/attendance", methods=["POST"])

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

    # Load or create attendance DataFrame
    df = load_attendance_df()
    if df.empty:
        return jsonify({"error": "attendance.xlsx is empty or missing student data."}), 500

    roll_to_name = get_roll_to_name(df)
    total_students = len(df)

    # Mark attendance for this session
    df["Total Classes"] = df.get("Total Classes", 0) + 1
    df["Total Present"] = df.get("Total Present", 0)
    for idx, row in df.iterrows():
        roll = row["Roll No"]
        if roll in absent_rolls:
            # Absent, do not increment present
            continue
        # Present or OD, increment present
        df.at[idx, "Total Present"] = row.get("Total Present", 0) + 1

    # Recalculate percentage
    df["Percentage"] = (df["Total Present"] / df["Total Classes"] * 100).round(2)
    save_attendance_df(df)

    present = total_students - len(absent_rolls)
    percentage = round((present / total_students) * 100)

    absentees = [
        f"{roll_to_name[r]} ({r})"
        for r in absent_rolls if r in roll_to_name
    ]

    ods = [
        f"{roll_to_name[r]} ({r})"
        for r in od_rolls if r in roll_to_name
    ]

    result = f"""Good morning sir,\nDate : {date}\nHour: {hour}\nII YEAR - A\nB.Tech IT  : {present}/{total_students}\n--------------------------------\nPercentage : {percentage}%\n\n *Absentees List\n"""
    for i, a in enumerate(absentees, 1):
        result += f"{i}. {a}\n"
    result += "\nOD\n"
    for i, o in enumerate(ods, 1):
        result += f"{i}. {o}\n"
    result += "\nThank you sir"

    return jsonify({"output": result})


if __name__ == "__main__":
    app.run()


# Endpoint to download the attendance.xlsx file
from flask import send_file

@app.route("/download-attendance", methods=["GET"])
def download_attendance():
    try:
        return send_file(ATTENDANCE_FILE, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
