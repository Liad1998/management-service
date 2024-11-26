const express = require('express');
const bodyParser = require('body-parser');
const app = express();

// Enable static files like HTML and JS
app.use(express.static('public'));

// Initial parameters
const SHIFTS = ["בוקר", "ערב", "לילה"];
const EMPLOYEES = ["אדם1", "אדם2", "אדם3", "אדם4", "אדם5", "אדם6", "אדם7"];
let RESTRICTIONS = {
    "אדם1": { "days": { 2: ["לילה"], 5: ["לילה"] } },
    "אדם2": { "days": { 3: [] } },
    "אדם3": { "days": {}, "shifts": ["בוקר"] }
};

// Configure Body Parser for JSON formats
app.use(bodyParser.json());

// Check employee availability for a shift
const isAvailable = (employee, day, shift, schedule) => {
    const restrictions = RESTRICTIONS[employee] || {};

    if (restrictions.days && Array.isArray(restrictions.days[day]) && restrictions.days[day].includes(shift)) {
        return false;
    }

    const nightShift = schedule[day]?.["לילה"] || [];
    const morningShift = schedule[day]?.["בוקר"] || [];

    if ((shift === "בוקר" && nightShift.includes(employee)) || 
        (shift === "לילה" && morningShift.includes(employee)) || 
        (schedule[day][shift] && schedule[day][shift].includes(employee))) {
        return false;
    }

    // Check if the employee is assigned to the previous or next shift
    const prevShift = shift === "בוקר" ? "לילה" : shift === "ערב" ? "בוקר" : "ערב";
    const nextShift = shift === "בוקר" ? "ערב" : shift === "ערב" ? "לילה" : "בוקר";

    if ((schedule[day][prevShift] && schedule[day][prevShift].includes(employee)) || 
        (schedule[day][nextShift] && schedule[day][nextShift].includes(employee))) {
        return false;
    }

    // Check if the employee is assigned to the previous night's shift
    if (day > 1) {
        const prevDayNightShift = schedule[day - 1]?.["לילה"] || [];
        if (shift === "בוקר" && prevDayNightShift.includes(employee)) {
            return false;
        }
    }

    return true;
};

// Custom function to randomly select an item from an array
const getRandomChoice = (array) => {
    return array[Math.floor(Math.random() * array.length)];
};

// Create shift schedule
const generateSchedule = () => {
    let schedule = {};
    for (let day = 1; day <= 7; day++) {
        schedule[day] = { "בוקר": [], "ערב": [], "לילה": [] };
    }

    let employeeShifts = Object.fromEntries(EMPLOYEES.map(employee => [employee, 0]));

    for (let day = 1; day <= 7; day++) {
        SHIFTS.forEach(shift => {
            let maxEmployees = (day === 6 || day === 7 || shift === "לילה") ? 1 : 2;
            let candidates = EMPLOYEES.filter(employee => 
                employeeShifts[employee] < 5 && isAvailable(employee, day, shift, schedule));

            while (schedule[day][shift].length < maxEmployees && candidates.length > 0) {
                let assigned = getRandomChoice(candidates);
                if (!schedule[day][shift].includes(assigned)) {
                    schedule[day][shift].push(assigned);
                    employeeShifts[assigned]++;
                }
                candidates = candidates.filter(c => c !== assigned);
            }
        });
    }

    // Ensure all employees work exactly 5 shifts
    EMPLOYEES.forEach(employee => {
        while (employeeShifts[employee] < 5) {
            for (let day = 1; day <= 7; day++) {
                SHIFTS.forEach(shift => {
                    if (isAvailable(employee, day, shift, schedule) && employeeShifts[employee] < 5) {
                        schedule[day][shift].push(employee);
                        employeeShifts[employee]++;
                    }
                });
            }
        }
    });

    return { schedule, employeeShifts };
};

// Route to generate shift schedule
app.get('/generate_schedule', (req, res) => {
    const { schedule, employeeShifts } = generateSchedule();

    let shiftsTable = "משמרות לכל עובד:<br>";
    Object.entries(employeeShifts).forEach(([employee, shiftCount]) => {
        shiftsTable += `${employee}: ${shiftCount} משמרות<br>`;
    });

    res.json({ "schedule": schedule, "shifts_table": shiftsTable });
});

// Route to update restrictions
app.post('/update_restrictions', (req, res) => {
    const { employee, restrictions } = req.body;

    if (EMPLOYEES.includes(employee)) {
        if (!RESTRICTIONS[employee]) {
            RESTRICTIONS[employee] = { "days": {} };
        }

        restrictions.forEach(({ day, shift }) => {
            if (!RESTRICTIONS[employee]["days"][day]) {
                RESTRICTIONS[employee]["days"][day] = [];
            }
            if (!RESTRICTIONS[employee]["days"][day].includes(shift)) {
                RESTRICTIONS[employee]["days"][day].push(shift);
            }
        });

        res.json({ "message": "Restrictions updated successfully" });
    } else {
        res.status(404).json({ "message": "Employee not found" });
    }
});

// Start server on port 3000
app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000');
});
