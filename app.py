from flask import Flask, jsonify, request, render_template
import random

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/restrictions')
def restrictions():
    return render_template('restrictions.html')

@app.route('/get_restrictions', methods=['GET'])
def get_restrictions():
    return jsonify(RESTRICTIONS)

# תנאים בסיסיים
SHIFTS = ["בוקר", "ערב", "לילה"]
SHIFT_HOURS = {"בוקר": (8, 17), "ערב": (15, 23), "לילה": (23, 8)}
EMPLOYEES = ["אדם1", "אדם2", "אדם3", "אדם4", "אדם5", "אדם6", "אדם7"]
RESTRICTIONS = {
    "אדם1": {"days": {2: ["לילה"], 5: ["לילה"]}},
    "אדם2": {"days": {3: []}},
    "אדם3": {"days": {}, "shifts": ["בוקר"]},
}

@app.route('/update_restrictions', methods=['POST'])
def update_restrictions():
    data = request.json
    employee = data.get('employee')
    day = int(data.get('day'))
    shift = data.get('shift')

    if employee in EMPLOYEES:
        if employee not in RESTRICTIONS:
            RESTRICTIONS[employee] = {"days": {}}
        if day not in RESTRICTIONS[employee]["days"]:
            RESTRICTIONS[employee]["days"][day] = []
        if shift not in RESTRICTIONS[employee]["days"][day]:
            RESTRICTIONS[employee]["days"][day].append(shift)
        return jsonify({"message": "Restrictions updated successfully"}), 200
    else:
        return jsonify({"message": "Employee not found"}), 404

def is_available(employee, day, shift, schedule):
    """בודקת אם העובד זמין ליום ומשמרת מסוימים בהתאם להגבלות"""
    restrictions = RESTRICTIONS.get(employee, {})
    if day in restrictions.get("days", {}) and shift in restrictions["days"].get(day, []):
        return False

    # בדיקת רציפות משמרות (אי אפשר בוקר ולילה באותו יום, ולא לילה ואז בוקר ביום למחרת)
    if shift == "בוקר" and (employee in schedule[day].get("לילה", []) or (day > 1 and employee in schedule[day-1].get("לילה", []))):
        return False
    if shift == "לילה" and (employee in schedule[day].get("בוקר", []) or (day < 7 and employee in schedule[day+1].get("בוקר", []))):
        return False
    if shift == "ערב" and employee in schedule[day].get("לילה", []):
        return False

    # בדיקה אם העובד עבד במשמרת הקודמת באותו יום (למניעת משמרות רצופות)
    previous_shift = SHIFTS[(SHIFTS.index(shift) - 1) % len(SHIFTS)]
    if employee in schedule[day].get(previous_shift, []):
        return False

    # בדיקת משמרות כפולות באותו יום
    if employee in schedule[day].get(shift, []):
        return False

    return True

def generate_schedule():
    schedule = {day: {"בוקר": [], "ערב": [], "לילה": []} for day in range(1, 8)}
    employee_shifts = {employee: 0 for employee in EMPLOYEES}

    for day in range(1, 8):
        for shift in SHIFTS:
            max_employees = 1 if day in [6, 7] or shift == "לילה" else 2
            candidates = [
                emp for emp in EMPLOYEES
                if employee_shifts[emp] < 5 and is_available(emp, day, shift, schedule)
            ]
            while len(schedule[day][shift]) < max_employees and candidates:
                assigned = random.choice(candidates)
                if assigned not in schedule[day][shift]:
                    schedule[day][shift].append(assigned)
                    employee_shifts[assigned] += 1
                candidates.remove(assigned)

    # השלמת משמרות ריקות
    for day in range(1, 8):
        for shift in SHIFTS:
            max_employees = 1 if day in [6, 7] or shift == "לילה" else 2
            while len(schedule[day][shift]) < max_employees:
                candidates = [
                    emp for emp in EMPLOYEES
                    if employee_shifts[emp] < 5 and is_available(emp, day, shift, schedule)
                ]
                if candidates:
                    assigned = random.choice(candidates)
                    if assigned not in schedule[day][shift]:
                        schedule[day][shift].append(assigned)
                        employee_shifts[assigned] += 1
                else:
                    break

    # הבטחת שכל העובדים יעבדו בדיוק חמש משמרות
    for employee in EMPLOYEES:
        while employee_shifts[employee] < 5:
            for day in range(1, 8):
                for shift in SHIFTS:
                    if is_available(employee, day, shift, schedule):
                        schedule[day][shift].append(employee)
                        employee_shifts[employee] += 1
                        if employee_shifts[employee] == 5:
                            break
                if employee_shifts[employee] == 5:
                    break

    return schedule, employee_shifts

@app.route('/generate_schedule', methods=['GET'])
def get_schedule():
    schedule, employee_shifts = generate_schedule()

    shifts_table = "משמרות לכל עובד:<br>"
    for employee, shift_count in employee_shifts.items():
        shifts_table += f"{employee}: {shift_count} משמרות<br>"

    return jsonify({"schedule": schedule, "shifts_table": shifts_table})

if __name__ == '__main__':
    app.run(debug=True)
