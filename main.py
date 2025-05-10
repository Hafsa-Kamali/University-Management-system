import streamlit as st
import pandas as pd
import sqlite3
import uuid
import os
from datetime import datetime
import altair as alt  # Added missing import for altair

# Setup page configuration
st.set_page_config(
    page_title="University Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def setup_database():
    conn = sqlite3.connect('university.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department_id TEXT,
        instructor_id TEXT,
        credits INTEGER,
        description TEXT,
        FOREIGN KEY (department_id) REFERENCES departments(id),
        FOREIGN KEY (instructor_id) REFERENCES instructors(id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS persons (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        email TEXT UNIQUE,
        type TEXT NOT NULL
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        roll_number TEXT UNIQUE NOT NULL,
        entry_year INTEGER,
        program TEXT,
        FOREIGN KEY (id) REFERENCES persons(id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS instructors (
        id TEXT PRIMARY KEY,
        salary REAL,
        department_id TEXT,
        position TEXT,
        FOREIGN KEY (id) REFERENCES persons(id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS enrollments (
        student_id TEXT,
        course_id TEXT,
        enrollment_date TEXT,
        grade TEXT,
        PRIMARY KEY (student_id, course_id),
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
    ''')
    
    conn.commit()
    return conn

# Create a connection to the database
conn = setup_database()

# Add some sample data if tables are empty
def add_sample_data():
    c = conn.cursor()
    
    # Check if departments table is empty
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        # Add sample departments
        departments = [
            (str(uuid.uuid4()), "Computer Science"),
            (str(uuid.uuid4()), "Mathematics"),
            (str(uuid.uuid4()), "Physics")
        ]
        c.executemany("INSERT INTO departments (id, name) VALUES (?, ?)", departments)
        
        # Get department IDs for reference
        c.execute("SELECT id, name FROM departments")
        dept_ids = {name: id for id, name in c.fetchall()}
        
        # Add sample persons who are instructors
        instructors = [
            (str(uuid.uuid4()), "Dr. John Smith", 45, "john.smith@university.edu", "instructor"),
            (str(uuid.uuid4()), "Dr. Jane Doe", 38, "jane.doe@university.edu", "instructor"),
            (str(uuid.uuid4()), "Prof. Robert Johnson", 55, "robert.johnson@university.edu", "instructor")
        ]
        c.executemany("INSERT INTO persons (id, name, age, email, type) VALUES (?, ?, ?, ?, ?)", instructors)
        
        # Get instructor IDs for reference
        instructor_ids = []
        for i in range(len(instructors)):
            c.execute("SELECT id FROM persons WHERE email = ?", (instructors[i][3],))
            instructor_ids.append(c.fetchone()[0])
        
        # Add instructor details
        instructor_details = [
            (instructor_ids[0], 85000, dept_ids["Computer Science"], "Associate Professor"),
            (instructor_ids[1], 78000, dept_ids["Mathematics"], "Assistant Professor"),
            (instructor_ids[2], 95000, dept_ids["Physics"], "Professor")
        ]
        c.executemany("INSERT INTO instructors (id, salary, department_id, position) VALUES (?, ?, ?, ?)", instructor_details)
        
        # Add sample courses
        courses = [
            (str(uuid.uuid4()), "Introduction to Programming", dept_ids["Computer Science"], instructor_ids[0], 3, "Basic programming concepts using Python"),
            (str(uuid.uuid4()), "Calculus I", dept_ids["Mathematics"], instructor_ids[1], 4, "Limits, derivatives, and integrals"),
            (str(uuid.uuid4()), "Classical Mechanics", dept_ids["Physics"], instructor_ids[2], 4, "Newton's laws and classical physics principles")
        ]
        c.executemany("INSERT INTO courses (id, name, department_id, instructor_id, credits, description) VALUES (?, ?, ?, ?, ?, ?)", courses)
        
        # Add sample students
        students = [
            (str(uuid.uuid4()), "Alice Johnson", 20, "alice.johnson@university.edu", "student"),
            (str(uuid.uuid4()), "Bob Williams", 21, "bob.williams@university.edu", "student"),
            (str(uuid.uuid4()), "Charlie Brown", 19, "charlie.brown@university.edu", "student")
        ]
        c.executemany("INSERT INTO persons (id, name, age, email, type) VALUES (?, ?, ?, ?, ?)", students)
        
        # Get student IDs for reference
        student_ids = []
        for i in range(len(students)):
            c.execute("SELECT id FROM persons WHERE email = ?", (students[i][3],))
            student_ids.append(c.fetchone()[0])
        
        # Add student details
        student_details = [
            (student_ids[0], "CS2023001", 2023, "BS Computer Science"),
            (student_ids[1], "MA2023002", 2023, "BS Mathematics"),
            (student_ids[2], "PH2023003", 2023, "BS Physics")
        ]
        c.executemany("INSERT INTO students (id, roll_number, entry_year, program) VALUES (?, ?, ?, ?)", student_details)
        
        # Get course IDs for enrollments
        c.execute("SELECT id FROM courses")
        course_ids = [row[0] for row in c.fetchall()]
        
        # Add enrollments
        enrollments = [
            (student_ids[0], course_ids[0], datetime.now().strftime("%Y-%m-%d"), None),
            (student_ids[0], course_ids[1], datetime.now().strftime("%Y-%m-%d"), None),
            (student_ids[1], course_ids[1], datetime.now().strftime("%Y-%m-%d"), None),
            (student_ids[2], course_ids[2], datetime.now().strftime("%Y-%m-%d"), None)
        ]
        c.executemany("INSERT INTO enrollments (student_id, course_id, enrollment_date, grade) VALUES (?, ?, ?, ?)", enrollments)
        
        conn.commit()

# Add sample data if needed
add_sample_data()

# Utility functions
def get_departments():
    return pd.read_sql_query("SELECT * FROM departments", conn)

def get_courses():
    query = """
    SELECT c.id, c.name, d.name as department, p.name as instructor, c.credits, c.description
    FROM courses c
    LEFT JOIN departments d ON c.department_id = d.id
    LEFT JOIN persons p ON c.instructor_id = p.id
    """
    return pd.read_sql_query(query, conn)

def get_students():
    query = """
    SELECT p.id, p.name, p.age, p.email, s.roll_number, s.entry_year, s.program
    FROM persons p
    JOIN students s ON p.id = s.id
    WHERE p.type = 'student'
    """
    return pd.read_sql_query(query, conn)

def get_instructors():
    query = """
    SELECT p.id, p.name, p.age, p.email, i.salary, d.name as department, i.position
    FROM persons p
    JOIN instructors i ON p.id = i.id
    LEFT JOIN departments d ON i.department_id = d.id
    WHERE p.type = 'instructor'
    """
    return pd.read_sql_query(query, conn)

def get_enrollments():
    query = """
    SELECT 
        e.student_id, 
        p.name as student_name, 
        s.roll_number,
        e.course_id, 
        c.name as course_name, 
        e.enrollment_date, 
        e.grade
    FROM enrollments e
    JOIN students s ON e.student_id = s.id
    JOIN persons p ON s.id = p.id
    JOIN courses c ON e.course_id = c.id
    """
    return pd.read_sql_query(query, conn)

def get_student_courses(student_id):
    query = """
    SELECT 
        c.id, 
        c.name, 
        d.name as department, 
        p.name as instructor, 
        c.credits, 
        e.enrollment_date,
        e.grade
    FROM enrollments e
    JOIN courses c ON e.course_id = c.id
    LEFT JOIN departments d ON c.department_id = d.id
    LEFT JOIN persons p ON c.instructor_id = p.id
    WHERE e.student_id = ?
    """
    return pd.read_sql_query(query, conn, params=(student_id,))

def get_instructor_courses(instructor_id):
    query = """
    SELECT 
        c.id, 
        c.name, 
        d.name as department, 
        c.credits, 
        c.description,
        (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id) as enrolled_students
    FROM courses c
    LEFT JOIN departments d ON c.department_id = d.id
    WHERE c.instructor_id = ?
    """
    return pd.read_sql_query(query, conn, params=(instructor_id,))

# Custom styling
def apply_custom_styles():
    st.markdown("""
    <style>
    .main-header {
        font-size: 38px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #1E3A8A;
    }
    .section-header {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .card {
        background-color: #F9FAFB;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .stat-box {
        background-color: #EFF6FF;
        border-left: 5px solid #1E3A8A;
        padding: 10px;
        margin-bottom: 10px;
    }
    .highlight {
        color: #1E3A8A;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Apply custom styles
apply_custom_styles()

# Sidebar navigation
st.sidebar.image("https://img.icons8.com/color/96/000000/university.png", width=80)
st.sidebar.markdown("<h2 style='text-align: center;'>University Management</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Sidebar menu
menu_options = ["Dashboard", "Students", "Instructors", "Courses", "Departments", "Enrollments", "Reports"]
menu_icons = ["📊", "👨‍🎓", "👨‍🏫", "📚", "🏢", "📝", "📈"]

menu_selection = st.sidebar.radio("", 
    options=menu_options,
    format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}")

st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 University Management System")

# Main content
st.markdown("<div class='main-header'>University Management System</div>", unsafe_allow_html=True)

# Dashboard
if menu_selection == "Dashboard":
    st.markdown("<div class='section-header'>System Overview</div>", unsafe_allow_html=True)
    
    # Overview statistics
    col1, col2, col3, col4 = st.columns(4)
    
    # Get counts for each entity
    student_count = len(get_students())
    instructor_count = len(get_instructors())
    course_count = len(get_courses())
    department_count = len(get_departments())
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h3>Students</h3><h2 class='highlight'>{student_count}</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h3>Instructors</h3><h2 class='highlight'>{instructor_count}</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h3>Courses</h3><h2 class='highlight'>{course_count}</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h3>Departments</h3><h2 class='highlight'>{department_count}</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent activity (placeholder)
    st.markdown("<div class='section-header'>Recent Activity</div>", unsafe_allow_html=True)
    
    # Mock recent activity data
    recent_activities = [
        {"type": "enrollment", "description": "Alice Johnson enrolled in Introduction to Programming", "timestamp": "2025-05-09 14:30:22"},
        {"type": "grade", "description": "Prof. Robert Johnson updated grades for Classical Mechanics", "timestamp": "2025-05-08 10:15:45"},
        {"type": "course", "description": "New course Advanced Database Systems added", "timestamp": "2025-05-07 16:22:10"},
        {"type": "student", "description": "New student David Wilson registered", "timestamp": "2025-05-06 09:05:38"}
    ]
    
    activity_df = pd.DataFrame(recent_activities)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.dataframe(activity_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Department statistics
    st.markdown("<div class='section-header'>Department Statistics</div>", unsafe_allow_html=True)
    
    # Count students and instructors per department
    c = conn.cursor()
    c.execute("""
    SELECT d.name as department, 
           COUNT(DISTINCT i.id) as instructor_count,
           (SELECT COUNT(DISTINCT s.id) 
            FROM students s 
            JOIN enrollments e ON s.id = e.student_id 
            JOIN courses c ON e.course_id = c.id 
            WHERE c.department_id = d.id) as student_count
    FROM departments d
    LEFT JOIN instructors i ON d.id = i.department_id
    GROUP BY d.name
    """)
    
    dept_stats = c.fetchall()
    dept_stats_df = pd.DataFrame(dept_stats, columns=["Department", "Instructors", "Students"])
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.bar_chart(dept_stats_df.set_index("Department"))
    st.markdown("</div>", unsafe_allow_html=True)

# Students section
elif menu_selection == "Students":
    st.markdown("<div class='section-header'>Student Management</div>", unsafe_allow_html=True)
    
    # Tabs for different student operations
    student_tabs = st.tabs(["View Students", "Add Student", "Student Details"])
    
    with student_tabs[0]:
        # View students
        students_df = get_students()
        st.dataframe(students_df, use_container_width=True, hide_index=True)
        
        # Export option
        if st.button("Export Students Data"):
            csv = students_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="students_data.csv",
                mime="text/csv"
            )
    
    with student_tabs[1]:
        # Add new student
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Add New Student")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=16, max_value=100, value=18)
            email = st.text_input("Email")
        
        with col2:
            roll_number = st.text_input("Roll Number")
            entry_year = st.number_input("Entry Year", min_value=2000, max_value=datetime.now().year, value=datetime.now().year)
            program = st.selectbox("Program", ["BS Computer Science", "BS Mathematics", "BS Physics", "BS Chemistry", "BA Economics", "Other"])
        
        if st.button("Add Student"):
            if name and email and roll_number:
                try:
                    # Check if roll number already exists
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM students WHERE roll_number = ?", (roll_number,))
                    if c.fetchone()[0] > 0:
                        st.error("Roll number already exists!")
                    else:
                        # Create a new student
                        student_id = str(uuid.uuid4())
                        
                        # Insert into persons table
                        c.execute("INSERT INTO persons (id, name, age, email, type) VALUES (?, ?, ?, ?, ?)",
                                 (student_id, name, age, email, "student"))
                        
                        # Insert into students table
                        c.execute("INSERT INTO students (id, roll_number, entry_year, program) VALUES (?, ?, ?, ?)",
                                 (student_id, roll_number, entry_year, program))
                        
                        conn.commit()
                        st.success("Student added successfully!")
                except Exception as e:
                    st.error(f"Error adding student: {e}")
            else:
                st.warning("Please fill in all required fields!")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with student_tabs[2]:
        # Student details and course registration
        students = get_students()
        student_names = students["name"].tolist()
        selected_student = st.selectbox("Select Student", student_names)
        
        if selected_student:
            student_id = students[students["name"] == selected_student]["id"].values[0]
            student_details = students[students["id"] == student_id]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Student Information")
                st.write(f"**Name:** {student_details['name'].values[0]}")
                st.write(f"**Roll Number:** {student_details['roll_number'].values[0]}")
                st.write(f"**Program:** {student_details['program'].values[0]}")
                st.write(f"**Entry Year:** {student_details['entry_year'].values[0]}")
                st.write(f"**Age:** {student_details['age'].values[0]}")
                st.write(f"**Email:** {student_details['email'].values[0]}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Course Registration")
                
                # Get courses the student is not enrolled in
                c = conn.cursor()
                c.execute("""
                SELECT c.id, c.name 
                FROM courses c 
                WHERE c.id NOT IN (
                    SELECT course_id FROM enrollments WHERE student_id = ?
                )
                """, (student_id,))
                
                available_courses = c.fetchall()
                
                if available_courses:
                    course_options = {course[1]: course[0] for course in available_courses}
                    selected_course = st.selectbox("Select Course to Register", list(course_options.keys()))
                    
                    if st.button("Register Course"):
                        course_id = course_options[selected_course]
                        try:
                            c.execute("INSERT INTO enrollments (student_id, course_id, enrollment_date, grade) VALUES (?, ?, ?, ?)",
                                     (student_id, course_id, datetime.now().strftime("%Y-%m-%d"), None))
                            conn.commit()
                            st.success(f"Successfully registered for {selected_course}!")
                        except Exception as e:
                            st.error(f"Error registering for course: {e}")
                else:
                    st.info("No available courses to register")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Show enrolled courses
            st.markdown("<div class='section-header'>Enrolled Courses</div>", unsafe_allow_html=True)
            
            student_courses = get_student_courses(student_id)
            if not student_courses.empty:
                st.dataframe(student_courses, use_container_width=True, hide_index=True)
                
                # Drop course option
                course_names = student_courses["name"].tolist()
                selected_course_to_drop = st.selectbox("Select Course to Drop", course_names)
                
                if st.button("Drop Course"):
                    course_id = student_courses[student_courses["name"] == selected_course_to_drop]["id"].values[0]
                    try:
                        c = conn.cursor()
                        c.execute("DELETE FROM enrollments WHERE student_id = ? AND course_id = ?", (student_id, course_id))
                        conn.commit()
                        st.success(f"Successfully dropped {selected_course_to_drop}!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error dropping course: {e}")
            else:
                st.info("Not enrolled in any courses")

# Instructors section
elif menu_selection == "Instructors":
    st.markdown("<div class='section-header'>Instructor Management</div>", unsafe_allow_html=True)
    
    # Tabs for different instructor operations
    instructor_tabs = st.tabs(["View Instructors", "Add Instructor", "Instructor Details"])
    
    with instructor_tabs[0]:
        # View instructors
        instructors_df = get_instructors()
        st.dataframe(instructors_df, use_container_width=True, hide_index=True)
        
        # Export option
        if st.button("Export Instructors Data"):
            csv = instructors_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="instructors_data.csv",
                mime="text/csv"
            )
    
    with instructor_tabs[1]:
        # Add new instructor
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Add New Instructor")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=22, max_value=100, value=35)
            email = st.text_input("Email")
        
        with col2:
            departments = get_departments()
            department_options = {row["name"]: row["id"] for _, row in departments.iterrows()}
            selected_department = st.selectbox("Department", list(department_options.keys()))
            position = st.selectbox("Position", ["Professor", "Associate Professor", "Assistant Professor", "Lecturer"])
            salary = st.number_input("Salary", min_value=0, value=75000)
        
        if st.button("Add Instructor"):
            if name and email:
                try:
                    # Create a new instructor
                    instructor_id = str(uuid.uuid4())
                    department_id = department_options[selected_department]
                    
                    # Insert into persons table
                    c = conn.cursor()
                    c.execute("INSERT INTO persons (id, name, age, email, type) VALUES (?, ?, ?, ?, ?)",
                             (instructor_id, name, age, email, "instructor"))
                    
                    # Insert into instructors table
                    c.execute("INSERT INTO instructors (id, salary, department_id, position) VALUES (?, ?, ?, ?)",
                             (instructor_id, salary, department_id, position))
                    
                    conn.commit()
                    st.success("Instructor added successfully!")
                except Exception as e:
                    st.error(f"Error adding instructor: {e}")
            else:
                st.warning("Please fill in all required fields!")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with instructor_tabs[2]:
        # Instructor details and course assignment
        instructors = get_instructors()
        instructor_names = instructors["name"].tolist()
        selected_instructor = st.selectbox("Select Instructor", instructor_names)
        
        if selected_instructor:
            instructor_id = instructors[instructors["name"] == selected_instructor]["id"].values[0]
            instructor_details = instructors[instructors["id"] == instructor_id]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Instructor Information")
                st.write(f"**Name:** {instructor_details['name'].values[0]}")
                st.write(f"**Position:** {instructor_details['position'].values[0]}")
                st.write(f"**Department:** {instructor_details['department'].values[0]}")
                st.write(f"**Age:** {instructor_details['age'].values[0]}")
                st.write(f"**Email:** {instructor_details['email'].values[0]}")
                st.write(f"**Salary:** ${instructor_details['salary'].values[0]:,.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Show courses taught
            st.markdown("<div class='section-header'>Courses Taught</div>", unsafe_allow_html=True)
            
            instructor_courses = get_instructor_courses(instructor_id)
            if not instructor_courses.empty:
                st.dataframe(instructor_courses, use_container_width=True, hide_index=True)
            else:
                st.info("Not teaching any courses")
            
            # Assign new course
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("Assign New Course")
            
            # Get courses not assigned to this instructor
            c = conn.cursor()
            c.execute("""
            SELECT c.id, c.name 
            FROM courses c 
            WHERE c.instructor_id IS NULL OR c.instructor_id != ?
            """, (instructor_id,))
            
            available_courses = c.fetchall()
            
            if available_courses:
                course_options = {course[1]: course[0] for course in available_courses}
                selected_course = st.selectbox("Select Course to Assign", list(course_options.keys()))
                
                if st.button("Assign Course"):
                    course_id = course_options[selected_course]
                    try:
                        c.execute("UPDATE courses SET instructor_id = ? WHERE id = ?", (instructor_id, course_id))
                        conn.commit()
                        st.success(f"Successfully assigned to teach {selected_course}!")
                    except Exception as e:
                        st.error(f"Error assigning course: {e}")
            else:
                st.info("No available courses to assign")
            st.markdown("</div>", unsafe_allow_html=True)

# Courses section
elif menu_selection == "Courses":
    st.markdown("<div class='section-header'>Course Management</div>", unsafe_allow_html=True)
    
    # Tabs for different course operations
    course_tabs = st.tabs(["View Courses", "Add Course", "Course Details"])
    
    with course_tabs[0]:
        # View courses
        courses_df = get_courses()
        st.dataframe(courses_df, use_container_width=True, hide_index=True)
        
        # Export option
        if st.button("Export Courses Data"):
            csv = courses_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="courses_data.csv",
                mime="text/csv"
            )
    
    with course_tabs[1]:
        # Add new course
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Add New Course")
        
        col1, col2 = st.columns(2)
        
        with col1:
            course_name = st.text_input("Course Name")
            credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
            description = st.text_area("Description")
        
        with col2:
            departments = get_departments()
            department_options = {row["name"]: row["id"] for _, row in departments.iterrows()}
            selected_department = st.selectbox("Department", list(department_options.keys()))
            
            instructors = get_instructors()
            instructor_options = {"None": None}
            instructor_options.update({row["name"]: row["id"] for _, row in instructors.iterrows()})
            selected_instructor = st.selectbox("Instructor", list(instructor_options.keys()))
        
        if st.button("Add Course"):
            if course_name and credits:
                try:
                    # Create a new course
                    course_id = str(uuid.uuid4())
                    department_id = department_options[selected_department]
                    instructor_id = instructor_options[selected_instructor]
                    
                    # Insert into courses table
                    c = conn.cursor()
                    c.execute("""
                    INSERT INTO courses (id, name, department_id, instructor_id, credits, description) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (course_id, course_name, department_id, instructor_id, credits, description))
                    
                    conn.commit()
                    st.success("Course added successfully!")
                except Exception as e:
                    st.error(f"Error adding course: {e}")
            else:
                st.warning("Please fill in all required fields!")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with course_tabs[2]:
        # Course details and enrollment management
        courses = get_courses()
        course_names = courses["name"].tolist()
        selected_course = st.selectbox("Select Course", course_names)
        
        if selected_course:
            course_id = courses[courses["name"] == selected_course]["id"].values[0]
            course_details = courses[courses["id"] == course_id]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Course Information")
                st.write(f"**Name:** {course_details['name'].values[0]}")
                st.write(f"**Department:** {course_details['department'].values[0]}")
                st.write(f"**Instructor:** {course_details['instructor'].values[0]}")
                st.write(f"**Credits:** {course_details['credits'].values[0]}")
                st.write(f"**Description:** {course_details['description'].values[0]}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Course Enrollment")
                
                # Get enrolled students
                c = conn.cursor()
                c.execute("""
                SELECT p.name, s.roll_number, e.enrollment_date, e.grade
                FROM enrollments e
                JOIN students s ON e.student_id = s.id
                JOIN persons p ON s.id = p.id
                WHERE e.course_id = ?
                """, (course_id,))
                
                enrolled_students = c.fetchall()
                
                if enrolled_students:
                    enrolled_df = pd.DataFrame(enrolled_students, columns=["Student Name", "Roll Number", "Enrollment Date", "Grade"])
                    st.dataframe(enrolled_df, use_container_width=True, hide_index=True)
                    
                    # Update grades
                    st.subheader("Update Grades")
                    student_options = [row[0] for row in enrolled_students]
                    selected_student = st.selectbox("Select Student", student_options)
                    
                    # Get current grade for the selected student
                    current_grade = None
                    for student in enrolled_students:
                        if student[0] == selected_student:
                            current_grade = student[3]
                            break
                    
                    grade_options = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", None]
                    selected_grade = st.selectbox("Select Grade", grade_options, index=grade_options.index(current_grade) if current_grade in grade_options else len(grade_options)-1)
                    
                    if st.button("Update Grade"):
                        try:
                            # Get student ID
                            c.execute("""
                            SELECT s.id 
                            FROM students s
                            JOIN persons p ON s.id = p.id
                            WHERE p.name = ?
                            """, (selected_student,))
                            student_id = c.fetchone()[0]
                            
                            c.execute("UPDATE enrollments SET grade = ? WHERE student_id = ? AND course_id = ?", 
                                    (selected_grade, student_id, course_id))
                            conn.commit()
                            st.success(f"Grade updated for {selected_student}!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error updating grade: {e}")
                else:
                    st.info("No students enrolled in this course")
                st.markdown("</div>", unsafe_allow_html=True)

# Departments section
elif menu_selection == "Departments":
    st.markdown("<div class='section-header'>Department Management</div>", unsafe_allow_html=True)
    
    # Tabs for different department operations
    dept_tabs = st.tabs(["View Departments", "Add Department", "Department Details"])
    
    with dept_tabs[0]:
        # View departments
        departments_df = get_departments()
        st.dataframe(departments_df, use_container_width=True, hide_index=True)
        
        # Export option
        if st.button("Export Departments Data"):
            csv = departments_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="departments_data.csv",
                mime="text/csv"
            )
    
    with dept_tabs[1]:
        # Add new department
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Add New Department")
        
        department_name = st.text_input("Department Name")
        
        if st.button("Add Department"):
            if department_name:
                try:
                    # Create a new department
                    department_id = str(uuid.uuid4())
                    
                    # Insert into departments table
                    c = conn.cursor()
                    c.execute("INSERT INTO departments (id, name) VALUES (?, ?)",
                             (department_id, department_name))
                    
                    conn.commit()
                    st.success("Department added successfully!")
                except Exception as e:
                    st.error(f"Error adding department: {e}")
            else:
                st.warning("Please enter a department name!")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with dept_tabs[2]:
        # Department details
        departments = get_departments()
        department_names = departments["name"].tolist()
        selected_department = st.selectbox("Select Department", department_names)
        
        if selected_department:
            department_id = departments[departments["name"] == selected_department]["id"].values[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Department Information")
                
                # Get department stats
                c = conn.cursor()
                c.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM instructors WHERE department_id = ?) as instructor_count,
                    (SELECT COUNT(*) FROM courses WHERE department_id = ?) as course_count,
                    (SELECT COUNT(DISTINCT e.student_id) 
                     FROM enrollments e 
                     JOIN courses c ON e.course_id = c.id 
                     WHERE c.department_id = ?) as student_count
                """, (department_id, department_id, department_id))
                
                stats = c.fetchone()
                
                st.write(f"**Name:** {selected_department}")
                st.write(f"**Instructors:** {stats[0]}")
                st.write(f"**Courses:** {stats[1]}")
                st.write(f"**Students Enrolled:** {stats[2]}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Department Courses")
                
                # Get department courses
                c.execute("""
                SELECT c.name, p.name as instructor, c.credits
                FROM courses c
                LEFT JOIN persons p ON c.instructor_id = p.id
                WHERE c.department_id = ?
                """, (department_id,))
                
                courses = c.fetchall()
                
                if courses:
                    courses_df = pd.DataFrame(courses, columns=["Course Name", "Instructor", "Credits"])
                    st.dataframe(courses_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No courses in this department")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Department instructors
            st.markdown("<div class='section-header'>Department Instructors</div>", unsafe_allow_html=True)
            
            c.execute("""
            SELECT p.name, i.position, i.salary
            FROM instructors i
            JOIN persons p ON i.id = p.id
            WHERE i.department_id = ?
            """, (department_id,))
            
            instructors = c.fetchall()
            
            if instructors:
                instructors_df = pd.DataFrame(instructors, columns=["Name", "Position", "Salary"])
                st.dataframe(instructors_df, use_container_width=True, hide_index=True)
            else:
                st.info("No instructors in this department")

# Enrollments section
elif menu_selection == "Enrollments":
    st.markdown("<div class='section-header'>Enrollment Management</div>", unsafe_allow_html=True)
    
    # View all enrollments
    enrollments_df = get_enrollments()
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        course_filter = st.selectbox("Filter by Course", ["All"] + list(enrollments_df["course_name"].unique()))
    
    with col2:
        student_filter = st.selectbox("Filter by Student", ["All"] + list(enrollments_df["student_name"].unique()))
    
    with col3:
        grade_filter = st.selectbox("Filter by Grade", ["All", "Graded", "Ungraded"] + 
                                  [g for g in enrollments_df["grade"].unique() if g is not None])
    
    # Apply filters
    if course_filter != "All":
        enrollments_df = enrollments_df[enrollments_df["course_name"] == course_filter]
    
    if student_filter != "All":
        enrollments_df = enrollments_df[enrollments_df["student_name"] == student_filter]
    
    if grade_filter == "Graded":
        enrollments_df = enrollments_df[enrollments_df["grade"].notna()]
    elif grade_filter == "Ungraded":
        enrollments_df = enrollments_df[enrollments_df["grade"].isna()]
    elif grade_filter != "All":
        enrollments_df = enrollments_df[enrollments_df["grade"] == grade_filter]
    
    # Display filtered enrollments
    st.dataframe(enrollments_df, use_container_width=True, hide_index=True)
    
    # Enrollment statistics
    st.markdown("<div class='section-header'>Enrollment Statistics</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Courses by Enrollment")
        
        # Get top courses by enrollment
        c = conn.cursor()
        c.execute("""
        SELECT c.name, COUNT(e.student_id) as enrollments
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        GROUP BY c.name
        ORDER BY enrollments DESC
        LIMIT 10
        """)
        
        top_courses = c.fetchall()
        
        if top_courses:
            top_courses_df = pd.DataFrame(top_courses, columns=["Course", "Enrollments"])
            st.bar_chart(top_courses_df.set_index("Course"))
        else:
            st.info("No enrollment data available")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Grade Distribution")
        
        # Get grade distribution
        c.execute("""
        SELECT grade, COUNT(*) as count
        FROM enrollments
        WHERE grade IS NOT NULL
        GROUP BY grade
        ORDER BY grade
        """)
        
        grades = c.fetchall()
        
        if grades:
            grades_df = pd.DataFrame(grades, columns=["Grade", "Count"])
            st.bar_chart(grades_df.set_index("Grade"))
        else:
            st.info("No grade data available")
        st.markdown("</div>", unsafe_allow_html=True)

# Reports section
elif menu_selection == "Reports":
    st.markdown("<div class='section-header'>System Reports</div>", unsafe_allow_html=True)
    
    # Report options
    report_options = {
        "Student Demographics": "Analyze student age distribution and programs",
        "Instructor Salary Analysis": "View salary distribution by department and position",
        "Course Popularity": "See which courses are most popular",
        "Department Comparison": "Compare departments by various metrics"
    }
    
    selected_report = st.selectbox("Select Report", list(report_options.keys()))
    
    if selected_report == "Student Demographics":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Student Demographics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Age distribution
            students = get_students()
            st.bar_chart(students["age"].value_counts().sort_index(), use_container_width=True)
            st.caption("Student Age Distribution")
        
        with col2:
            # Program distribution
            program_counts = students["program"].value_counts()
            st.bar_chart(program_counts, use_container_width=True)
            st.caption("Student Program Distribution")
        
        # Entry year analysis
        st.subheader("Entry Year Analysis")
        entry_year_counts = students["entry_year"].value_counts().sort_index()
        st.line_chart(entry_year_counts, use_container_width=True)
        st.caption("Students by Entry Year")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif selected_report == "Instructor Salary Analysis":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Instructor Salary Analysis")
        
        # Salary by position
        instructors = get_instructors()
        salary_by_position = instructors.groupby("position")["salary"].mean().sort_values(ascending=False)
        st.bar_chart(salary_by_position, use_container_width=True)
        st.caption("Average Salary by Position")
        
        # Salary by department
        salary_by_dept = instructors.groupby("department")["salary"].mean().sort_values(ascending=False)
        st.bar_chart(salary_by_dept, use_container_width=True)
        st.caption("Average Salary by Department")
        
        # Salary distribution
        st.subheader("Salary Distribution")
        st.altair_chart(alt.Chart(instructors).mark_bar().encode(
            alt.X("salary:Q", bin=True),
            y='count()',
        ), use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif selected_report == "Course Popularity":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Course Popularity")
        
        # Get course enrollments
        c = conn.cursor()
        c.execute("""
        SELECT c.name, d.name as department, COUNT(e.student_id) as enrollments
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN departments d ON c.department_id = d.id
        GROUP BY c.name
        ORDER BY enrollments DESC
        """)
        
        course_popularity = c.fetchall()
        
        if course_popularity:
            popularity_df = pd.DataFrame(course_popularity, columns=["Course", "Department", "Enrollments"])
            
            # Top 10 courses
            st.subheader("Top 10 Courses by Enrollment")
            top_10 = popularity_df.head(10)
            st.bar_chart(top_10.set_index("Course"))
            
            # By department
            st.subheader("Enrollments by Department")
            dept_enrollments = popularity_df.groupby("Department")["Enrollments"].sum().sort_values(ascending=False)
            st.bar_chart(dept_enrollments)
        else:
            st.info("No enrollment data available")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif selected_report == "Department Comparison":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Department Comparison")
        
        # Get department stats
        c = conn.cursor()
        c.execute("""
        SELECT 
            d.name as department,
            COUNT(DISTINCT i.id) as instructors,
            COUNT(DISTINCT c.id) as courses,
            (SELECT COUNT(DISTINCT e.student_id) 
             FROM enrollments e 
             JOIN courses co ON e.course_id = co.id 
             WHERE co.department_id = d.id) as students
        FROM departments d
        LEFT JOIN instructors i ON d.id = i.department_id
        LEFT JOIN courses c ON d.id = c.department_id
        GROUP BY d.name
        """)
        
        dept_stats = c.fetchall()
        
        if dept_stats:
            dept_stats_df = pd.DataFrame(dept_stats, columns=["Department", "Instructors", "Courses", "Students"])
            
            # Comparison metrics
            metric = st.selectbox("Select Metric", ["Instructors", "Courses", "Students"])
            
            if metric:
                st.bar_chart(dept_stats_df.set_index("Department")[metric])
                
                # Detailed comparison
                st.subheader("Detailed Comparison")
                st.dataframe(dept_stats_df.set_index("Department"), use_container_width=True)
        else:
            st.info("No department data available")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Add some space at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)