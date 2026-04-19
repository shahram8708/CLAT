import json
import os
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import bleach

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.result import Result
from app.models.scholarship_question import ScholarshipQuestion
from app.models.site_setting import SiteSetting
from app.models.test_series import TestSeries
from app.models.user import User

ALLOWED_TAGS = [
    'p',
    'h2',
    'h3',
    'ul',
    'ol',
    'li',
    'strong',
    'em',
    'a',
    'table',
    'thead',
    'tbody',
    'tr',
    'th',
    'td',
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'target', 'rel'],
}


def sanitize_html(content):
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=['http', 'https', 'mailto'],
        strip=True,
    )


def upsert_record(model, lookup, values):
    record = model.query.filter_by(**lookup).first()
    created = False
    if not record:
        record = model(**lookup)
        db.session.add(record)
        created = True

    for key, value in values.items():
        setattr(record, key, value)

    return record, created


def seed_admin_user():
    admin_values = {
        'first_name': 'Admin',
        'last_name': 'CL Ahmedabad',
        'phone': '9978559986',
        'role': 'admin',
        'is_active': True,
    }
    admin, created = upsert_record(User, {'email': 'admin@clahmedabad.com'}, admin_values)

    if created or not admin.password_hash or not admin.check_password('Admin@CL2026!'):
        admin.set_password('Admin@CL2026!')

    return admin


def seed_faculty_data():
    faculty_entries = [
        {
            'slug': 'bhavik-thakkar',
            'name': 'Bhavik Thakkar',
            'title': 'Quantitative Aptitude & DI-LR Expert',
            'qualification': 'B.Sc Mathematics, Gold Medallist',
            'exam_score': '99.99 Percentile in CAT',
            'experience_yrs': 15,
            'subjects': ['Quantitative Aptitude', 'Data Interpretation', 'Logical Reasoning'],
            'exam_tags': ['CAT', 'IPMAT', 'GMAT', 'CUET'],
            'bio_short': '15+ years training CAT aspirants. Has personally mentored 1,000+ students who achieved 99+ percentile. Known for his structured approach to complex Quant problems.',
            'bio_long': dedent('''
                Bhavik Thakkar has spent over fifteen years building one of the most reliable Quant and LRDI classrooms for management entrance aspirants in Ahmedabad. A gold medallist in Mathematics, he brings deep conceptual rigor and practical test strategy to every session. Students appreciate his ability to simplify difficult arithmetic and algebra blocks into predictable frameworks that can be solved under strict exam time pressure.

                In his classroom process, concept explanation is only the first step. Every chapter is followed by graded drills, timed application sets, and post test error correction. Bhavik tracks how students attempt a question, where they lose time, and how decision making changes under pressure. This method has helped hundreds of aspirants move from average mock scores to consistently high percentile performance.

                Beyond content delivery, he is known for personal mentoring and confidence building. Students who struggle with Quant anxiety receive custom revision pathways, speed building routines, and weekly diagnostics that keep progress visible. His mentoring has contributed to a large number of 99+ percentile outcomes and has made him one of the most trusted CAT educators at Career Launcher Ahmedabad.
            ''').strip(),
            'display_order': 1,
            'is_active': True,
        },
        {
            'slug': 'akshit-mishra',
            'name': 'Akshit Mishra',
            'title': 'VARC, Legal Reasoning & GK Expert',
            'qualification': 'LLB (Hons), PhD (Law), Practising Advocate',
            'exam_score': '99+ Percentile in CLAT | Advocate + PhD Scholar',
            'experience_yrs': 10,
            'subjects': ['Verbal Ability', 'Reading Comprehension', 'Legal Reasoning', 'General Knowledge', 'Current Affairs'],
            'exam_tags': ['CLAT', 'AILET', 'SLAT', 'NLAT'],
            'bio_short': 'Practising advocate and PhD scholar leading CLAT/AILET preparation. His students hold 6 of the top 10 ranks in CLAT 2025.',
            'bio_long': dedent('''
                Akshit Mishra brings a rare blend of legal practice, academic depth, and competitive exam mentorship to the CLAT and AILET classroom. As a practising advocate and doctoral scholar in Law, he teaches legal reasoning with strong real world context. His classes help students understand principle based questions not as memory exercises but as logical application tasks built on interpretation and structured judgment.

                His pedagogy combines close reading discipline, argument mapping, and current legal developments to improve both speed and precision. In English and critical reasoning sessions, he trains students to identify question intent quickly, eliminate deceptive options, and maintain accuracy across long passages. For GK and current affairs, his weekly briefings focus on high utility topics and retention techniques that support long term recall.

                Akshit is especially known for interview stage mentoring and exam temperament coaching. Students receive realistic mock environments, strategy corrections, and confidence support for high pressure phases. His results driven approach has played an important role in multiple top rank outcomes and has positioned him as a key mentor for law entrance aspirants in Ahmedabad.
            ''').strip(),
            'display_order': 2,
            'is_active': True,
        },
        {
            'slug': 'hemant-gajaria',
            'name': 'Hemant Gajaria',
            'title': 'Mathematics & Quantitative Specialist',
            'qualification': 'B.Tech (Electronics Engineering)',
            'exam_score': 'B.Tech Graduate | Mathematics Specialist',
            'experience_yrs': 8,
            'subjects': ['Mathematics', 'Arithmetic', 'Algebra', 'Calculus', 'Statistics'],
            'exam_tags': ['IPMAT', 'CUET', 'Boards', 'GMAT'],
            'bio_short': 'Engineering graduate specialising in Mathematics for IPMAT, CUET, and Class XI–XII Board examinations.',
            'bio_long': dedent('''
                Hemant Gajaria is an engineering graduate who has dedicated his teaching career to mathematics mastery for undergraduate entrances and board examinations. His sessions cover arithmetic fundamentals, algebraic fluency, and higher level applications in a sequence that supports both weak and advanced learners. He focuses on making mathematical thinking visual, structured, and repeatable for students from varied academic backgrounds.

                For IPMAT and CUET aspirants, Hemant designs problem sets that balance concept depth with exam level execution speed. Every topic includes baseline practice, medium level integration, and challenge rounds to develop confidence under timed conditions. In school mathematics programs, he emphasizes concept clarity first, then builds answer presentation quality, which helps students perform better in both objective and descriptive assessment formats.

                Students value his calm mentoring style and precision in doubt solving. He tracks learning gaps chapter wise and uses focused revision plans before major tests. His contribution to the Ahmedabad centre has strengthened mathematics outcomes across IPMAT, CUET, and board oriented batches, making him a dependable mentor for students targeting strong quantitative performance.
            ''').strip(),
            'display_order': 3,
            'is_active': True,
        },
        {
            'slug': 'chandraveer-jain',
            'name': 'Chandraveer Jain',
            'title': 'LRDI & Quantitative Aptitude Expert',
            'qualification': 'MBA, IIM Kozhikode',
            'exam_score': '99+ Percentile in CAT | MBA from IIM Kozhikode',
            'experience_yrs': 7,
            'subjects': ['Logical Reasoning', 'Data Interpretation', 'Quantitative Aptitude'],
            'exam_tags': ['CAT', 'CLAT', 'IPMAT', 'XAT'],
            'bio_short': 'IIM Kozhikode alumnus delivering structured LRDI training. Renowned for his unique pattern-recognition method.',
            'bio_long': dedent('''
                Chandraveer Jain is an IIM Kozhikode alumnus with deep expertise in LRDI and Quant preparation for aptitude based entrance exams. His teaching model focuses on pattern recognition and decision sequencing, two areas that significantly improve score outcomes in difficult test sections. Students learn how to select sets intelligently, avoid traps, and allocate time based on expected return.

                In LRDI classes, he deconstructs complex caselets into visual structures and logic maps that reduce cognitive load. In Quant, he emphasizes alternative methods and shortcut validation, helping students solve with confidence without sacrificing accuracy. His assignments are designed around real exam behavior, so learners build practical judgment and not just theoretical familiarity.

                Chandraveer also mentors students on strategic planning, mock review discipline, and recovery after low scoring tests. His balanced approach of rigor plus motivation has helped many students progress steadily through preparation cycles. At Career Launcher Ahmedabad, he is widely recognized for turning uncertain aspirants into consistent performers through method driven teaching.
            ''').strip(),
            'display_order': 4,
            'is_active': True,
        },
    ]

    for item in faculty_entries:
        values = dict(item)
        values['subjects'] = json.dumps(item['subjects'], ensure_ascii=False)
        values['exam_tags'] = json.dumps(item['exam_tags'], ensure_ascii=False)
        values.pop('slug', None)
        upsert_record(Faculty, {'slug': item['slug']}, values)


def seed_course_data():
    courses = [
        {
            'slug': 'cat-mba',
            'title': 'CAT / MBA Entrance',
            'exam_category': 'CAT',
            'exams_covered': ['CAT', 'XAT', 'SNAP', 'NMAT', 'CMAT', 'MAH-CET'],
            'description': "Master CAT, XAT, SNAP, NMAT & more with India's most experienced coaching team.",
            'long_description': 'A comprehensive CAT and MBA entrance training program with concept classes, sectional workshops, full length mocks, and GD-PI-WAT support.',
            'duration': '10-12 Months',
            'mode': 'hybrid',
            'batch_size': 25,
            'fee_min': 55000,
            'fee_max': 150000,
            'icon': '🎓',
            'display_order': 1,
            'syllabus_json': [
                {'subject': 'Quantitative Aptitude', 'topics': ['Arithmetic', 'Algebra', 'Geometry', 'Number Systems', 'Modern Maths', 'Data Sufficiency']},
                {'subject': 'Verbal Ability & Reading Comprehension', 'topics': ['Reading Comprehension', 'Para Jumbles', 'Summary', 'Odd Sentence Out', 'Vocabulary', 'Critical Reasoning']},
                {'subject': 'Data Interpretation & Logical Reasoning', 'topics': ['Tables', 'Bar Charts', 'Line Graphs', 'Pie Charts', 'Caselets', 'Seating Arrangement', 'Blood Relations', 'Syllogisms', 'Puzzles']},
            ],
        },
        {
            'slug': 'clat-ailet',
            'title': 'CLAT / AILET / Law Entrance',
            'exam_category': 'CLAT',
            'exams_covered': ['CLAT', 'AILET', 'SLAT', 'NLAT', 'MAH-CET Law'],
            'description': 'Comprehensive CLAT + AILET + SLAT coaching with 6/10 top CLAT 2025 ranks.',
            'long_description': 'Law entrance coaching with legal reasoning mastery, reading comprehension drills, GK updates, and timed sectional practices.',
            'duration': '6-12 Months',
            'mode': 'classroom',
            'batch_size': 20,
            'fee_min': 45000,
            'fee_max': 80000,
            'icon': '⚖️',
            'display_order': 2,
            'syllabus_json': [
                {'subject': 'English Language', 'topics': ['Reading Comprehension', 'Grammar', 'Vocabulary', 'Para Completion', 'Critical Reasoning']},
                {'subject': 'Legal Reasoning', 'topics': ['Legal Principles', 'Torts', 'Contracts', 'Constitutional Law', 'Criminal Law', 'Case Studies']},
                {'subject': 'Logical Reasoning', 'topics': ['Analogies', 'Series', 'Coding-Decoding', 'Blood Relations', 'Syllogisms', 'Arrangements']},
                {'subject': 'Quantitative Techniques', 'topics': ['Arithmetic', 'Data Interpretation', 'Basic Algebra', 'Statistics']},
                {'subject': 'General Knowledge & Current Affairs', 'topics': ['National Events', 'International Affairs', 'Legal Current Affairs', 'Science & Tech', 'Awards & Honours']},
            ],
        },
        {
            'slug': 'ipmat-bba',
            'title': 'IPMAT / BBA Entrance',
            'exam_category': 'IPMAT',
            'exams_covered': ['IPMAT', 'Nirma BBA', 'CUSAT BBA', 'IPUCET', 'DU JAT'],
            'description': 'Dedicated small-batch coaching for IPMAT, Nirma BBA, and other BBA entrances.',
            'long_description': 'IPMAT and BBA preparation with quantitative strengthening, verbal development, and interview readiness sessions.',
            'duration': '6-10 Months',
            'mode': 'classroom',
            'batch_size': 15,
            'fee_min': 40000,
            'fee_max': 70000,
            'icon': '🏛️',
            'display_order': 3,
            'syllabus_json': [
                {'subject': 'Quantitative Aptitude', 'topics': ['Arithmetic', 'Algebra', 'Geometry', 'Number Theory', 'Data Interpretation', 'Modern Mathematics']},
                {'subject': 'Verbal Ability', 'topics': ['Reading Comprehension', 'Grammar', 'Vocabulary', 'Para Jumbles', 'Fill in the Blanks']},
                {'subject': 'Logical Reasoning', 'topics': ['Puzzles', 'Arrangements', 'Analogies', 'Series', 'Blood Relations', 'Directions']},
                {'subject': 'General Awareness', 'topics': ['Current Events', 'Business & Economics', 'Awards', 'Famous Personalities']},
            ],
        },
        {
            'slug': 'gmat-gre',
            'title': 'GMAT / GRE Study Abroad',
            'exam_category': 'GMAT',
            'exams_covered': ['GMAT', 'GRE'],
            'description': 'Personalised 1-on-1 GMAT & GRE coaching for admissions to global top-50 B-Schools.',
            'long_description': 'One to one GMAT and GRE training plans with diagnostic mapping, adaptive testing, and profile support for applications.',
            'duration': 'Flexible (3-6 Months)',
            'mode': 'online',
            'batch_size': 5,
            'fee_min': 60000,
            'fee_max': 120000,
            'icon': '🌍',
            'display_order': 4,
            'syllabus_json': [
                {'subject': 'Quantitative Reasoning', 'topics': ['Problem Solving', 'Data Sufficiency', 'Arithmetic', 'Algebra', 'Geometry', 'Statistics']},
                {'subject': 'Verbal Reasoning', 'topics': ['Critical Reasoning', 'Sentence Correction', 'Reading Comprehension', 'Text Completion', 'Sentence Equivalence']},
                {'subject': 'Analytical Writing', 'topics': ['Issue Essay', 'Argument Essay', 'Writing Structure', 'Evidence Usage']},
                {'subject': 'Integrated Reasoning (GMAT)', 'topics': ['Multi-Source Reasoning', 'Table Analysis', 'Graphics Interpretation', 'Two-Part Analysis']},
            ],
        },
        {
            'slug': 'cuet',
            'title': 'CUET (Central University Entrance)',
            'exam_category': 'CUET',
            'exams_covered': ['CUET-UG', 'CUET-PG'],
            'description': 'Complete CUET preparation for top central universities + domain-specific subjects.',
            'long_description': 'Comprehensive CUET coaching that combines language, domain, and general test preparation with regular mocks.',
            'duration': '4-6 Months',
            'mode': 'hybrid',
            'batch_size': 30,
            'fee_min': 30000,
            'fee_max': 50000,
            'icon': '📚',
            'display_order': 5,
            'syllabus_json': [
                {'subject': 'General Test', 'topics': ['Numerical Ability', 'Reasoning', 'General Awareness', 'Current Affairs', 'Language Comprehension']},
                {'subject': 'Domain Subjects', 'topics': ['Mathematics', 'Accountancy', 'Business Studies', 'Economics', 'Political Science', 'History', 'Geography']},
                {'subject': 'Language Section', 'topics': ['Reading Comprehension', 'Literary Aptitude', 'Vocabulary', 'Grammar']},
            ],
        },
        {
            'slug': 'class-xi-xii-maths',
            'title': 'Class XI–XII Mathematics',
            'exam_category': 'Boards',
            'exams_covered': ['CBSE', 'ICSE', 'JEE Mains (Maths)'],
            'description': 'Board-focused + competitive Maths coaching. Builds foundation for IIT-JEE Maths too.',
            'long_description': 'Year long mathematics coaching for school success while building a strong base for aptitude and engineering entrances.',
            'duration': 'Full Academic Year',
            'mode': 'classroom',
            'batch_size': 15,
            'fee_min': 20000,
            'fee_max': 40000,
            'icon': '📐',
            'display_order': 6,
            'syllabus_json': [
                {'subject': 'Class XI Mathematics', 'topics': ['Sets & Functions', 'Algebra', 'Coordinate Geometry', 'Calculus', 'Mathematical Reasoning', 'Statistics & Probability']},
                {'subject': 'Class XII Mathematics', 'topics': ['Relations & Functions', 'Algebra (Matrices & Determinants)', 'Calculus (Differentiation & Integration)', 'Vectors & 3D Geometry', 'Linear Programming', 'Probability']},
                {'subject': 'JEE Maths (Foundation)', 'topics': ['Complex Numbers', 'Sequence & Series', 'Permutations & Combinations', 'Binomial Theorem', 'Trigonometry', 'Conic Sections']},
            ],
        },
    ]

    for item in courses:
        values = {
            'title': item['title'],
            'exam_category': item['exam_category'],
            'exams_covered': json.dumps(item['exams_covered'], ensure_ascii=False),
            'description': item['description'],
            'long_description': item['long_description'],
            'duration': item['duration'],
            'mode': item['mode'],
            'batch_size': item['batch_size'],
            'fee_min': item['fee_min'],
            'fee_max': item['fee_max'],
            'icon': item['icon'],
            'syllabus_json': json.dumps(item['syllabus_json'], ensure_ascii=False),
            'is_active': True,
            'display_order': item['display_order'],
        }
        upsert_record(Course, {'slug': item['slug']}, values)


def seed_result_data():
    results = [
        {'student_name': 'Shantanu', 'exam': 'CAT', 'year': 2024, 'rank_percentile': '99.61 %ile', 'target_college': 'IIM Ahmedabad', 'testimonial': "CL Ahmedabad's structured approach and Bhavik sir's Quant sessions transformed my preparation completely.", 'display_order': 1},
        {'student_name': 'Kathan Mehta', 'exam': 'CAT', 'year': 2024, 'rank_percentile': '98.2 %ile', 'target_college': 'IIM Bangalore', 'testimonial': 'The mock test analysis and peer benchmarking helped me identify and eliminate my weak areas.', 'display_order': 2},
        {'student_name': 'Phoenix', 'exam': 'CLAT', 'year': 2025, 'rank_percentile': 'AIR 7', 'target_college': 'GNLU Gandhinagar', 'testimonial': "Akshit sir's legal reasoning classes gave me the edge in CLAT 2025. Highly recommended.", 'display_order': 3},
        {'student_name': 'Ananya Shah', 'exam': 'CLAT', 'year': 2025, 'rank_percentile': 'AIR 3', 'target_college': 'NLSIU Bengaluru', 'testimonial': 'Best coaching for CLAT in Ahmedabad, no doubt.', 'display_order': 4},
        {'student_name': 'Dhruv Patel', 'exam': 'IPMAT', 'year': 2024, 'rank_percentile': 'AIR 12', 'target_college': 'IIM Indore (IPM)', 'testimonial': 'Small batch size at CL meant personal attention from day one.', 'display_order': 5},
        {'student_name': 'Riya Modi', 'exam': 'CLAT', 'year': 2025, 'rank_percentile': 'AIR 9', 'target_college': 'NLU Delhi', 'testimonial': 'The GK and current affairs updates were exceptional for CLAT.', 'display_order': 6},
        {'student_name': 'Aryan Trivedi', 'exam': 'CAT', 'year': 2024, 'rank_percentile': '99.94 %ile', 'target_college': 'IIM Ahmedabad', 'testimonial': "Bhavik sir's Quant sessions completely changed my approach.", 'display_order': 7},
        {'student_name': 'Priya Desai', 'exam': 'CAT', 'year': 2024, 'rank_percentile': '99.12 %ile', 'target_college': 'IIM Calcutta', 'testimonial': 'The AFA model let me attend classes from home during COVID recovery.', 'display_order': 8},
        {'student_name': 'Nikhil Sharma', 'exam': 'CLAT', 'year': 2025, 'rank_percentile': 'AIR 5', 'target_college': 'GNLU Gandhinagar', 'testimonial': 'Faculty quality at CL Ahmedabad is genuinely world-class.', 'display_order': 9},
        {'student_name': 'Sakshi Jain', 'exam': 'CAT', 'year': 2024, 'rank_percentile': '97.8 %ile', 'target_college': 'IIM Kozhikode', 'testimonial': 'The mock benchmarking against 3L+ students gave real exam-day confidence.', 'display_order': 10},
    ]

    for item in results:
        lookup = {
            'student_name': item['student_name'],
            'exam': item['exam'],
            'year': item['year'],
        }
        values = {
            'photo_url': None,
            'rank_percentile': item['rank_percentile'],
            'target_college': item['target_college'],
            'testimonial': item['testimonial'],
            'display_order': item['display_order'],
            'is_active': True,
        }
        upsert_record(Result, lookup, values)


def seed_blog_posts(admin_user):
    clat_syllabus_2027 = dedent('''
        <h2>CLAT 2027 Syllabus: What You Must Prepare</h2>
        <p>CLAT preparation becomes far easier when students understand that the exam is fundamentally a reading intensive aptitude test with legal and current affairs orientation. The syllabus is not officially released as a chapter list by the consortium, so aspirants should work with section level competencies. For CLAT 2027, this means mastering passage reading speed, inference accuracy, legal principle application, numerical comfort at school level, and disciplined current affairs revision. Students who start early should use the first three months for skill building and the remaining months for test simulation and refinement.</p>
        <p>The English Language section is built around comprehension passages. Questions check interpretation, tone, vocabulary in context, inference, and argument understanding. The most effective method is to read editorials and analytical long form writing daily, then solve mixed passage sets under time limits. Grammar rules matter, but the exam rewards comprehension more than isolated rule memorization. Students should maintain an error log that tracks why wrong options looked attractive because this improves elimination judgment quickly.</p>
        <p>Legal Reasoning is often the highest leverage section for rank movement. CLAT no longer rewards static legal trivia as much as principle based reasoning through passages. Students should learn how to apply a given principle to varied fact situations, identify exceptions, and evaluate competing interpretations. Good preparation includes regular legal passage practice, constitutional and legal current affairs reading, and discussion based classes where multiple answer approaches are evaluated. The goal is clarity of reasoning, not decorative legal vocabulary.</p>
        <p>Logical Reasoning in CLAT focuses on critical reasoning through text based prompts. You need to identify assumptions, strengthen or weaken claims, infer conclusions, and detect argument flaws. This section rewards calm reading and structured thinking. A practical routine is to solve smaller sets daily and revisit mistakes by tagging them into categories such as assumption error, quantifier confusion, and premature inference. Over time, this mistake taxonomy becomes a powerful revision tool before mocks.</p>
        <p>Quantitative Techniques uses basic mathematics and data interpretation usually through short sets. Required topics include arithmetic operations, percentages, ratio proportion, averages, simple equations, and table or chart interpretation. Students do not need advanced mathematics, but they do need speed and calculation discipline. Practicing with timed mini sets and mental approximation methods can improve confidence. Many students lose marks here because they postpone quant practice, so even humanities students should include daily quant drills from the beginning.</p>
        <p>General Knowledge and Current Affairs should be prepared with a rolling monthly system. Build notes across national policy updates, judiciary and legal developments, international events, awards, science and technology, business highlights, and sports. Instead of passive reading, aspirants should convert updates into short question prompts and revise them weekly. Monthly compendiums are useful, but they work best when combined with daily current affairs tracking and objective quizzes that test retention quality.</p>
        <h3>Suggested CLAT 2027 Preparation Timeline</h3>
        <ul>
          <li><strong>Phase 1 (Months 1 to 3):</strong> Build reading stamina, legal basics, arithmetic comfort, and current affairs note making.</li>
          <li><strong>Phase 2 (Months 4 to 7):</strong> Increase sectional practice, start weekly full length tests, and maintain a structured error register.</li>
          <li><strong>Phase 3 (Months 8 to 10):</strong> Focus on mock frequency, strategy tuning, and section specific time allocation.</li>
          <li><strong>Phase 4 (Final Months):</strong> Intensive revision, current affairs consolidation, and test day temperament training.</li>
        </ul>
        <p>A common CLAT mistake is collecting too many study resources and finishing none. Use limited trusted sources and revise repeatedly. Another mistake is avoiding full mocks until late in preparation. Mocks are not just score checks; they are strategy laboratories where you learn attempt order, question selection, and recovery after difficult sections. Students should review every mock deeply, including the questions they got right, to identify whether marks came from method or lucky elimination.</p>
        <p>At Career Launcher Ahmedabad, CLAT mentoring combines legal reasoning workshops, current affairs curation, and timed test analysis so students improve consistently. The right syllabus understanding plus disciplined execution can significantly improve your CLAT 2027 outcome. Keep preparation simple, measurable, and revision heavy. If you commit to daily reading, weekly testing, and monthly strategy correction, you can enter the final phase with confidence and rank readiness.</p>
    ''').strip()

    cat_working_professionals = dedent('''
        <h2>CAT Preparation Strategy for Working Professionals: A Practical 6 Month Plan</h2>
        <p>Working professionals preparing for CAT face a different challenge compared with full time students. Time is limited, energy varies across weekdays, and consistency often breaks due to office deadlines. The good news is that CAT rewards smart preparation structure more than long random study hours. A focused six month plan with realistic weekly targets, high quality mocks, and disciplined revision can produce excellent percentile outcomes. The strategy below is built for professionals managing jobs while aiming for serious CAT performance.</p>
        <p>The first principle is time blocking. Instead of waiting for large free slots, divide your week into fixed study windows. Most professionals can protect two weekday slots of ninety minutes each and one longer weekend block. This gives approximately twelve to fifteen productive hours per week, which is enough when used correctly. Keep weekdays concept and sectional focused, and reserve weekends for integrated practice and mock analysis. Avoid over scheduling that fails after two weeks.</p>
        <p>Months one and two should focus on concept rebuilding and diagnostic mapping. Begin with a baseline mock to understand current standing, then prioritize weak areas. In Quant, revisit arithmetic and algebra first because they contribute heavily and support many mixed problems. In VARC, practice reading comprehension daily and build a note based approach to passage tone and argument structure. In DILR, start with foundational set types and learn visual organization methods before speed attempts.</p>
        <p>Months three and four are transition months where sectional intensity increases. At this stage, every concept should be linked with timed practice. Solve medium and difficult questions in controlled sets and track error patterns by category. For VARC, focus on option elimination quality and para based question sequencing. For DILR, train selection discipline by scanning set complexity before solving. For Quant, improve decision making on question skip versus solve choices, because attempt quality drives percentile.</p>
        <p>Months five and six are mock dominated. Working professionals should aim for one full length mock every week in month five and two mocks per week in month six if schedule allows. The value of mocks lies in review depth. Spend more time analyzing than attempting. Identify section wise opportunity loss, question type traps, time distribution errors, and emotional decisions made under pressure. Then convert findings into actionable changes for the next mock cycle.</p>
        <h3>Weekly Template for Busy Professionals</h3>
        <ul>
          <li><strong>Monday:</strong> Quant concept revision plus timed arithmetic set.</li>
          <li><strong>Tuesday:</strong> VARC reading comprehension drills and option elimination review.</li>
          <li><strong>Wednesday:</strong> DILR set practice with selection strategy notes.</li>
          <li><strong>Thursday:</strong> Mixed sectional test and error log update.</li>
          <li><strong>Friday:</strong> Light revision and formula plus vocabulary consolidation.</li>
          <li><strong>Saturday or Sunday:</strong> Full mock and detailed analysis.</li>
        </ul>
        <p>Energy management is critical for professionals. Choose study slots that match your cognitive rhythm. Early morning learners should do problem solving before work. Night learners should avoid heavy screens before study and use short warm up drills to switch context from office to preparation. Keep at least one half day in the week for recovery to prevent burnout. Sustainable consistency beats short bursts of overwork followed by long gaps.</p>
        <p>Another important dimension is exam temperament. Professionals often underperform in mocks because of pressure to prove progress quickly. Do not chase score spikes. Track process metrics instead: accuracy in attempted questions, section wise time adherence, and reduction in repeated error types. Percentile rises naturally when process quality improves. Build confidence through repeatable routines rather than motivational highs that vanish after difficult tests.</p>
        <p>Career Launcher Ahmedabad mentors many working professionals through time efficient plans, performance dashboards, and personalized intervention. With the right six month strategy, even a demanding job schedule can coexist with strong CAT preparation. Stay consistent, review honestly, and keep the plan realistic. That combination delivers results.</p>
    ''').strip()

    ipmat_vs_bba = dedent('''
        <h2>IPMAT vs Other BBA Entrance Exams: Which Should You Appear For?</h2>
        <p>Students aiming for management after class twelve often ask whether they should prepare only for IPMAT or keep multiple BBA entrance exams in the plan. The practical answer depends on academic profile, comfort with mathematics, long term career goals, and risk tolerance. IPMAT offers a premium integrated pathway through selected IIMs, while other BBA entrances provide excellent alternatives through top private and university programs. A balanced strategy can improve admission probability without diluting preparation quality.</p>
        <p>IPMAT is highly competitive and typically tests stronger quantitative and verbal aptitude compared with many conventional BBA exams. Students who are comfortable with higher level arithmetic, algebra, and reasoning usually find IPMAT preparation intellectually rewarding. The exam demands speed, conceptual depth, and careful section balancing. If your target is an integrated management route with early exposure to rigorous academics, IPMAT should be central in your preparation plan.</p>
        <p>Other BBA entrance exams such as NPAT, SET, CUET aligned management pathways, and university specific tests may vary in difficulty and section composition. Some emphasize speed and breadth, while others test straightforward school level aptitude with general awareness components. These exams often provide multiple attempt opportunities and diverse institute choices. Students who want wider admission options should include selected non IPMAT exams to reduce dependency on a single high competition outcome.</p>
        <p>The smartest approach is to identify overlap and build a common preparation core. Reading comprehension, logical reasoning, arithmetic fundamentals, and data interpretation are shared across most tests. Once this base is strong, allocate exam specific slots each week for unique patterns. For example, if one exam has more vocabulary and another has more quantitative intensity, create targeted mini modules rather than restarting preparation separately for each exam.</p>
        <h3>Decision Framework for Students and Parents</h3>
        <ul>
          <li><strong>Academic Strength:</strong> If Quant is a strong area, prioritize IPMAT and add two to three backup BBA exams.</li>
          <li><strong>Career Preference:</strong> If you want broad institute options, apply across private and university led BBA pathways.</li>
          <li><strong>Risk Balance:</strong> Avoid a single exam strategy unless your mock performance is consistently exceptional.</li>
          <li><strong>Budget and Logistics:</strong> Track exam fees, city travel, and date clashes before finalizing applications.</li>
        </ul>
        <p>Another key factor is interview readiness. Some BBA and integrated management admissions include personal interview rounds. Students should therefore build communication clarity, profile storytelling, and current affairs understanding during written test preparation itself. This integrated preparation saves time later and improves final conversion chances. Ignoring interview readiness until after results is a common error that affects strong written performers.</p>
        <p>Students also need realistic mock test sequencing. Attempting too many mocks from different exams without analysis creates confusion. Instead, choose one primary exam format for weekly full mocks and add one secondary format every two weeks. Maintain separate error logs but track shared weaknesses such as careless arithmetic, rushed reading, or poor question selection. This keeps preparation coherent while still covering multiple admissions routes.</p>
        <p>For students in Ahmedabad, a blended preparation plan often works best: IPMAT focused foundation with strategic inclusion of other BBA entrances. This structure offers ambition plus safety. Career Launcher Ahmedabad supports this through exam wise roadmaps, small batch mentoring, and personalized mock feedback so students can make informed application decisions and maximize admission outcomes.</p>
    ''').strip()

    nlu_rankings_2025 = dedent('''
        <h2>Top NLUs in India 2025: Rankings, Fees, and Placement Perspective</h2>
        <p>Choosing a law school should not be reduced to one ranking list. A better approach is to evaluate a combination of academic rigor, faculty depth, internship culture, alumni outcomes, and total cost of education. In India, National Law Universities remain the preferred destination for CLAT aspirants because of structured legal curriculum and strong professional exposure. However, students should compare institutions using recent official disclosures instead of relying only on social media narratives.</p>
        <p>The most consistently discussed top group generally includes NLSIU Bengaluru, NALSAR Hyderabad, WBNUJS Kolkata, NLU Jodhpur, GNLU Gandhinagar, MNLU Mumbai, and NLU Delhi through its separate entrance route. The exact order can vary by metric such as litigation orientation, corporate placement profile, and research ecosystem. Aspirants should therefore map ranking context to personal goals. A student targeting corporate law may prioritize different indicators than someone inclined toward litigation or policy.</p>
        <p>Fee structures across NLUs vary significantly. Publicly available figures suggest integrated five year law programs at leading NLUs can range from moderate to high annual cost depending on tuition, hostel, and mandatory charges. Families should assess complete five year outflow and include inflation expectations. Many universities offer need based support and scholarships, so checking current financial aid policies is essential before final preference filling.</p>
        <h3>Indicative Comparison Snapshot</h3>
        <table>
          <thead>
            <tr><th>Institution</th><th>General Position</th><th>Typical Fee Band</th><th>Placement Outlook</th></tr>
          </thead>
          <tbody>
            <tr><td>NLSIU Bengaluru</td><td>Consistently top tier</td><td>Higher band</td><td>Strong corporate and litigation exposure</td></tr>
            <tr><td>NALSAR Hyderabad</td><td>Top tier</td><td>Higher band</td><td>Strong national recruiter visibility</td></tr>
            <tr><td>WBNUJS Kolkata</td><td>Top tier</td><td>Mid to higher band</td><td>Good corporate placement history</td></tr>
            <tr><td>NLU Jodhpur</td><td>Top tier</td><td>Mid to higher band</td><td>Strong business law orientation</td></tr>
            <tr><td>GNLU Gandhinagar</td><td>Upper tier</td><td>Mid band</td><td>Strong internships and growing placements</td></tr>
            <tr><td>MNLU Mumbai</td><td>Upper to mid tier</td><td>Mid to higher band</td><td>Location advantage for internships</td></tr>
            <tr><td>RMLNLU Lucknow</td><td>Upper to mid tier</td><td>Mid band</td><td>Steady placement and alumni network</td></tr>
            <tr><td>HNLU Raipur</td><td>Upper to mid tier</td><td>Mid band</td><td>Balanced litigation and corporate exposure</td></tr>
          </tbody>
        </table>
        <p>The table above provides an indicative planning view and should be cross checked with the latest official university notifications, annual reports, and verified placement disclosures. Students should always verify current fee circulars and seat matrices before final application decisions.</p>
        <p>Placements are best interpreted beyond highest package headlines. Evaluate median compensation, proportion of batch placed through campus processes, internship conversion rates, and role diversity. Some NLUs offer very strong outcomes for top quartile students but wider variability in the full cohort. This makes peer quality, academic discipline, and personal initiative equally important to institutional reputation.</p>
        <p>Location can influence internship opportunities but should not overshadow academic fit. Cities with stronger legal ecosystems may offer easier access to law firms and chambers during semester breaks. At the same time, students in non metro campuses can still build excellent profiles through remote internships, research projects, moot participation, and network building if they plan early and consistently.</p>
        <p>For CLAT aspirants targeting NLUs in 2025 and beyond, preference strategy should combine realistic score range, category wise seat availability, financial planning, and long term career alignment. Career Launcher Ahmedabad mentors students through this decision stage with counseling support, so final choices are informed by both data and personal fit. The right law school is the one where you can sustain high academic performance, build practical skills, and create strong professional outcomes over five years.</p>
    ''').strip()

    iim_ahmedabad_process = dedent('''
        <h2>IIM Ahmedabad Admission Process 2025: CAT Score, WAT PI, and Final Selection</h2>
        <p>IIM Ahmedabad remains one of the most aspirational management destinations in India, and naturally the admission process is highly selective. Many students believe that a very high CAT percentile alone is enough, but the institute follows a multi stage evaluation model. Understanding each stage clearly helps aspirants prepare in a focused manner. The process typically includes shortlisting based on CAT and profile parameters, followed by written and interview assessment, and then final composite score based merit.</p>
        <p>The first stage is CAT based shortlisting. A strong percentile is necessary, but sectional balance is equally important because minimum section wise cutoffs usually apply. Candidates should aim for consistency across VARC, DILR, and QA rather than over relying on one high scoring section. Along with CAT performance, institutes generally consider profile dimensions such as academic consistency and category specific criteria while preparing interview shortlists.</p>
        <p>Once shortlisted, candidates move into the written and interview phase. Different years may use different formats, but the broad objective is similar: assess clarity of thought, communication, analytical depth, and suitability for management learning. Students should prepare for structured writing on current affairs, business, economy, and social issues. Writing quality is judged on logic, coherence, and relevance, not ornamental language.</p>
        <p>The personal interview is a crucial differentiator. Panelists evaluate awareness, decision making ability, learning orientation, and authenticity of profile claims. Candidates should be ready with clear answers on academic journey, work experience impact, major projects, strengths, failures, and career goals. Generic rehearsed responses do not work well at this level. Honest, specific, and reflective communication usually leaves stronger impact than memorized templates.</p>
        <h3>What Final Selection Usually Rewards</h3>
        <ul>
          <li><strong>CAT Performance:</strong> High percentile with healthy section wise balance.</li>
          <li><strong>Academic Profile:</strong> Consistency across school and graduation stages.</li>
          <li><strong>Diversity Signals:</strong> Academic and professional diversity can influence weightage.</li>
          <li><strong>Interview Quality:</strong> Clarity, composure, and evidence based responses.</li>
          <li><strong>Writing Ability:</strong> Structured thinking and coherent articulation.</li>
        </ul>
        <p>Working professionals should highlight measurable contributions at work, not just role titles. Discuss impact through outcomes, process improvements, leadership moments, and learning from setbacks. Freshers should strengthen profile through internships, projects, competitions, and thoughtful career positioning. In both cases, awareness of current economic and business developments is essential for meaningful interview conversation.</p>
        <p>Another common mistake is beginning WAT PI preparation only after interview calls are announced. This leaves very little time for improvement. Students should start early with weekly writing practice, mock interviews, and profile introspection notes. Recording and reviewing mock responses can help improve structure and confidence quickly. Preparation should include both domain fundamentals and broad awareness topics.</p>
        <p>At Career Launcher Ahmedabad, CAT mentorship includes interview readiness support so students transition smoothly from percentile building to final selection preparation. The key is to treat admission as a complete process, not a single exam event. Strong CAT performance opens the door, but thoughtful profile presentation and interview execution decide final conversion outcomes at top institutes like IIM Ahmedabad.</p>
    ''').strip()

    scholarship_tips = dedent('''
        <h2>How to Win a Coaching Scholarship: CL Ahmedabad Scholarship Test Guide</h2>
        <p>Scholarship tests are one of the best ways for serious students to reduce fee burden while entering high quality coaching programs. Yet many aspirants approach scholarship exams casually and miss the opportunity. A scholarship test should be treated as a focused aptitude assessment where speed, accuracy, and clarity of basics matter more than advanced tricks. With the right strategy, students can significantly improve scholarship percentage and secure strong preparation support at lower cost.</p>
        <p>The first step is understanding the test pattern and scoring logic. Scholarship assessments usually include verbal reasoning, quantitative aptitude, logical puzzles, and general awareness. Some tests include reading comprehension and basic decision making scenarios. Students should request official syllabus guidance, section timing structure, and negative marking rules before starting preparation. Knowing the format removes uncertainty and helps you allocate study time intelligently.</p>
        <p>Preparation should begin with diagnostics. Attempt one sample paper under timed conditions, then classify mistakes into conceptual, speed, and attention errors. Conceptual errors require topic revision, speed errors require repeated timed drills, and attention errors require process discipline such as rechecking calculations and reading questions fully. This targeted correction approach improves score faster than solving random question banks without analysis.</p>
        <p>For quantitative sections, focus on arithmetic fundamentals first: percentages, ratio proportion, averages, profit and loss, time and work, simple interest, and data interpretation basics. In verbal sections, improve comprehension through daily reading and short inference questions. In reasoning sections, practice arrangements, syllogisms, coding decoding, and statement conclusion types. For general awareness, maintain concise weekly notes instead of memorizing disconnected facts.</p>
        <h3>Scholarship Test Week Plan</h3>
        <ul>
          <li><strong>Day 1:</strong> Quant fundamentals plus short timed quiz.</li>
          <li><strong>Day 2:</strong> Verbal and reading comprehension practice.</li>
          <li><strong>Day 3:</strong> Logical reasoning set work and error analysis.</li>
          <li><strong>Day 4:</strong> General awareness revision and mock quiz.</li>
          <li><strong>Day 5:</strong> Mixed section mini test with strict timing.</li>
          <li><strong>Day 6:</strong> Full scholarship mock and deep review.</li>
          <li><strong>Day 7:</strong> Light revision and confidence reset.</li>
        </ul>
        <p>During the actual test, begin with sections where your confidence is highest. Build early momentum and avoid spending too much time on one difficult question. Mark uncertain questions for review and keep moving. Scholarship tests reward balanced performance, so protecting easy marks is often more important than chasing a few difficult ones. Time discipline and calm decision making can create a big score advantage over equally prepared students.</p>
        <p>After the exam, keep required documents and communication details ready for counseling. Scholarships are usually tied to timeline based admission formalities, so quick follow through matters. Students should discuss batch options, mode preferences, and study schedule before final enrollment. A scholarship is not only a discount; it is also a commitment to consistent preparation and responsible academic engagement.</p>
        <p>Career Launcher Ahmedabad conducts scholarship pathways to make quality coaching more accessible for motivated students. If you prepare with a clear plan and test temperament, strong scholarship outcomes are realistic. Treat the scholarship exam as the first step of your preparation journey, and use it to start with confidence, structure, and accountability.</p>
    ''').strip()

    posts = [
        {
            'category': 'clat',
            'slug': 'clat-syllabus-2027',
            'title': 'CLAT 2027 Syllabus — Complete Subject-Wise Breakdown',
            'content': clat_syllabus_2027,
            'excerpt': 'Understand the CLAT 2027 syllabus section by section with a practical preparation timeline and high impact strategy.',
            'meta_title': 'CLAT 2027 Syllabus Complete Subject-Wise Breakdown',
            'meta_description': 'Detailed CLAT 2027 syllabus coverage for English, Legal Reasoning, Logical Reasoning, Quant and GK with prep timeline.',
        },
        {
            'category': 'cat',
            'slug': 'cat-preparation-strategy',
            'title': 'CAT Preparation Strategy for Working Professionals — 6-Month Plan',
            'content': cat_working_professionals,
            'excerpt': 'A realistic six month CAT plan for working professionals with time blocking, mocks, and weekly execution structure.',
            'meta_title': 'CAT Preparation Strategy for Working Professionals 6-Month Plan',
            'meta_description': 'Working professionals can crack CAT with this practical 6 month strategy covering quant, VARC, DILR and mock analysis.',
        },
        {
            'category': 'ipmat',
            'slug': 'ipmat-vs-bba-entrance-guide',
            'title': 'IPMAT vs Other BBA Entrance Exams — Which Should You Appear For?',
            'content': ipmat_vs_bba,
            'excerpt': 'Compare IPMAT with other BBA entrance exams and choose the right application strategy based on profile and goals.',
            'meta_title': 'IPMAT vs Other BBA Entrance Exams Complete Guide',
            'meta_description': 'Know the difference between IPMAT and other BBA exams and build a smart admission strategy with balanced risk.',
        },
        {
            'category': 'clat',
            'slug': 'top-nlus-india-2025',
            'title': 'Top NLUs in India 2025 — Complete Rankings, Fees & Placement Data',
            'content': nlu_rankings_2025,
            'excerpt': 'An informed look at top NLUs, fee planning, and placement interpretation for CLAT aspirants targeting law admissions.',
            'meta_title': 'Top NLUs in India 2025 Rankings Fees Placement Guide',
            'meta_description': 'Review top NLU options for 2025 with ranking context, fee bands, and placement considerations for CLAT students.',
        },
        {
            'category': 'cat',
            'slug': 'iim-ahmedabad-admission-process',
            'title': 'IIM Ahmedabad Admission Process 2025 — CAT Score, WAT-PI, Final Selection',
            'content': iim_ahmedabad_process,
            'excerpt': 'Learn how IIM Ahmedabad admission works from CAT shortlisting to interview and final composite score evaluation.',
            'meta_title': 'IIM Ahmedabad Admission Process 2025 CAT WAT PI',
            'meta_description': 'Understand IIM Ahmedabad admission stages including CAT score impact, WAT PI preparation, and final selection factors.',
        },
        {
            'category': 'general',
            'slug': 'scholarship-tips-coaching',
            'title': 'How to Win a Coaching Scholarship — CL Ahmedabad Scholarship Test Guide',
            'content': scholarship_tips,
            'excerpt': 'A practical scholarship test preparation guide covering section strategy, weekly planning, and test day execution.',
            'meta_title': 'How to Win a Coaching Scholarship CL Ahmedabad Guide',
            'meta_description': 'Prepare for coaching scholarship tests with focused strategy across quant, verbal, reasoning, and awareness sections.',
        },
    ]

    for post in posts:
        values = {
            'title': post['title'],
            'category': post['category'],
            'content': sanitize_html(post['content']),
            'excerpt': post['excerpt'],
            'featured_image': None,
            'author_id': admin_user.id,
            'meta_title': post['meta_title'],
            'meta_description': post['meta_description'],
            'is_published': True,
            'published_at': datetime.utcnow(),
        }
        upsert_record(BlogPost, {'slug': post['slug']}, values)


def seed_test_series_data():
    test_series_entries = [
        {'name': 'CLAT Full Mock 2026', 'exam': 'CLAT', 'description': 'Comprehensive CLAT mock pack with all major section distributions.', 'total_tests': 10, 'duration_mins': 120, 'is_free': False, 'price': 999},
        {'name': 'CLAT Free Trial Mock', 'exam': 'CLAT', 'description': 'One full CLAT mock test for benchmark analysis.', 'total_tests': 1, 'duration_mins': 120, 'is_free': True, 'price': None},
        {'name': 'CAT Full Mock Series 2025', 'exam': 'CAT', 'description': 'CAT level test series with percentile based diagnostics.', 'total_tests': 20, 'duration_mins': 120, 'is_free': False, 'price': 1499},
        {'name': 'CAT Free Sectional Mock', 'exam': 'CAT', 'description': 'Section wise CAT practice tests for speed building.', 'total_tests': 3, 'duration_mins': 40, 'is_free': True, 'price': None},
        {'name': 'IPMAT Mock Series 2026', 'exam': 'IPMAT', 'description': 'Targeted IPMAT test series for quantitative and verbal sections.', 'total_tests': 8, 'duration_mins': 90, 'is_free': False, 'price': 799},
        {'name': 'CUET Mock Test Pack', 'exam': 'CUET', 'description': 'CUET focused mixed section mock package.', 'total_tests': 5, 'duration_mins': 60, 'is_free': False, 'price': 499},
    ]

    for item in test_series_entries:
        values = {
            'exam': item['exam'],
            'description': item['description'],
            'total_tests': item['total_tests'],
            'duration_mins': item['duration_mins'],
            'is_free': item['is_free'],
            'price': item['price'],
            'razorpay_plan_id': None,
            'is_active': True,
        }
        upsert_record(TestSeries, {'name': item['name']}, values)


def seed_scholarship_questions():
    if ScholarshipQuestion.query.count() != 0:
        return

    questions = [
        {
            'question_text': 'What is 25 percent of 480?',
            'option_a': '110',
            'option_b': '120',
            'option_c': '125',
            'option_d': '140',
            'correct_answer': 'b',
            'subject': 'arithmetic',
            'display_order': 1,
        },
        {
            'question_text': 'The average of 12, 18, 24, and 30 is:',
            'option_a': '20',
            'option_b': '21',
            'option_c': '22',
            'option_d': '24',
            'correct_answer': 'b',
            'subject': 'arithmetic',
            'display_order': 2,
        },
        {
            'question_text': 'The ratio of boys to girls in a class is 7:5. If there are 96 students in total, how many girls are there?',
            'option_a': '35',
            'option_b': '38',
            'option_c': '40',
            'option_d': '42',
            'correct_answer': 'c',
            'subject': 'arithmetic',
            'display_order': 3,
        },
        {
            'question_text': 'A book priced at ₹2,000 is sold at a 15 percent discount. What is the selling price?',
            'option_a': '₹1,650',
            'option_b': '₹1,700',
            'option_c': '₹1,725',
            'option_d': '₹1,800',
            'correct_answer': 'b',
            'subject': 'arithmetic',
            'display_order': 4,
        },
        {
            'question_text': 'If x:y = 3:4 and x = 27, then y is:',
            'option_a': '32',
            'option_b': '34',
            'option_c': '36',
            'option_d': '40',
            'correct_answer': 'c',
            'subject': 'arithmetic',
            'display_order': 5,
        },
        {
            'question_text': 'Find the next number in the series: 2, 5, 10, 17, 26, ?',
            'option_a': '35',
            'option_b': '36',
            'option_c': '37',
            'option_d': '38',
            'correct_answer': 'c',
            'subject': 'reasoning',
            'display_order': 6,
        },
        {
            'question_text': 'Book is to Read as Food is to:',
            'option_a': 'Cook',
            'option_b': 'Serve',
            'option_c': 'Eat',
            'option_d': 'Smell',
            'correct_answer': 'c',
            'subject': 'reasoning',
            'display_order': 7,
        },
        {
            'question_text': 'Pointing to a girl, Ravi said, She is the daughter of my mother\'s only son. How is the girl related to Ravi?',
            'option_a': 'Sister',
            'option_b': 'Daughter',
            'option_c': 'Niece',
            'option_d': 'Cousin',
            'correct_answer': 'b',
            'subject': 'reasoning',
            'display_order': 8,
        },
        {
            'question_text': 'If CAT is coded as DBU, then DOG will be coded as:',
            'option_a': 'DNG',
            'option_b': 'EPH',
            'option_c': 'EOH',
            'option_d': 'FPH',
            'correct_answer': 'b',
            'subject': 'reasoning',
            'display_order': 9,
        },
        {
            'question_text': 'If all roses are flowers and all flowers are plants, which conclusion is correct?',
            'option_a': 'All plants are roses',
            'option_b': 'Some roses are not plants',
            'option_c': 'All roses are plants',
            'option_d': 'No flower is a plant',
            'correct_answer': 'c',
            'subject': 'reasoning',
            'display_order': 10,
        },
        {
            'question_text': 'Choose the synonym of abundant.',
            'option_a': 'Scarce',
            'option_b': 'Plentiful',
            'option_c': 'Uncertain',
            'option_d': 'Harsh',
            'correct_answer': 'b',
            'subject': 'verbal',
            'display_order': 11,
        },
        {
            'question_text': 'Fill in the blank: Despite the heavy rain, the match continued ____ interruption.',
            'option_a': 'without',
            'option_b': 'with',
            'option_c': 'under',
            'option_d': 'beyond',
            'correct_answer': 'a',
            'subject': 'verbal',
            'display_order': 12,
        },
        {
            'question_text': 'Choose the grammatically correct sentence.',
            'option_a': 'He don\'t like coffee.',
            'option_b': 'She has completed her homework.',
            'option_c': 'They was going to market.',
            'option_d': 'I am agree with you.',
            'correct_answer': 'b',
            'subject': 'verbal',
            'display_order': 13,
        },
        {
            'question_text': 'Passage: The library opens at 8 AM and students who arrive early get quieter study spaces. What can be inferred?',
            'option_a': 'The library is closed in the morning.',
            'option_b': 'Early arrival can improve concentration.',
            'option_c': 'Students are not allowed before noon.',
            'option_d': 'Only teachers can use the library.',
            'correct_answer': 'b',
            'subject': 'verbal',
            'display_order': 14,
        },
        {
            'question_text': 'Choose the antonym of expand.',
            'option_a': 'Increase',
            'option_b': 'Develop',
            'option_c': 'Contract',
            'option_d': 'Stretch',
            'correct_answer': 'c',
            'subject': 'verbal',
            'display_order': 15,
        },
        {
            'question_text': 'Which exam is used for admission to National Law Universities in India?',
            'option_a': 'CAT',
            'option_b': 'CLAT',
            'option_c': 'NEET',
            'option_d': 'GATE',
            'correct_answer': 'b',
            'subject': 'general_awareness',
            'display_order': 16,
        },
        {
            'question_text': 'CAT exam is conducted by:',
            'option_a': 'NTA',
            'option_b': 'UPSC',
            'option_c': 'Indian Institutes of Management',
            'option_d': 'AICTE',
            'correct_answer': 'c',
            'subject': 'general_awareness',
            'display_order': 17,
        },
        {
            'question_text': 'IIM stands for:',
            'option_a': 'Indian Institute of Management',
            'option_b': 'International Institute of Management',
            'option_c': 'Indian Institute of Marketing',
            'option_d': 'Integrated Institute of Management',
            'correct_answer': 'a',
            'subject': 'general_awareness',
            'display_order': 18,
        },
        {
            'question_text': 'CLAT full form is:',
            'option_a': 'Common Law Admission Test',
            'option_b': 'Central Law Aptitude Test',
            'option_c': 'Combined Legal Assessment Test',
            'option_d': 'Career Law Admission Test',
            'correct_answer': 'a',
            'subject': 'general_awareness',
            'display_order': 19,
        },
        {
            'question_text': 'What is IPMAT?',
            'option_a': 'Integrated Program Management and Training',
            'option_b': 'Indian Program for Management Aptitude Test',
            'option_c': 'Integrated Programme in Management Aptitude Test',
            'option_d': 'Institute Program for Managerial Assessment Test',
            'correct_answer': 'c',
            'subject': 'general_awareness',
            'display_order': 20,
        },
    ]

    db.session.add_all([ScholarshipQuestion(**question) for question in questions])


def seed_site_settings(admin_user):
    default_settings = {
        "institute_name": ("Career Launcher Ahmedabad", "text", "Institute Name", "contact"),
        "address": ("A 102, Karmyog Heights, Navrangpura, Ahmedabad - 380009", "textarea", "Address", "contact"),
        "phone_primary": ("+919978559986", "phone", "Primary Phone", "contact"),
        "phone_secondary": ("+916353842725", "phone", "Secondary Phone", "contact"),
        "email": ("cl_ahmedabad@careerlauncher.com", "email", "Email", "contact"),
        "whatsapp_number": ("919978559986", "phone", "WhatsApp Number", "contact"),
        "hours_weekday": ("Mon-Sat 10AM-7PM", "text", "Weekday Hours", "contact"),
        "hours_sunday": ("Sun 9AM-6PM", "text", "Sunday Hours", "contact"),
        "instagram_url": ("https://www.instagram.com/careerlauncher", "url", "Instagram URL", "social"),
        "youtube_url": ("https://www.youtube.com/@careerlauncher", "url", "YouTube URL", "social"),
        "facebook_url": ("https://www.facebook.com/CareerLauncher", "url", "Facebook URL", "social"),
        "linkedin_url": ("https://www.linkedin.com/company/career-launcher", "url", "LinkedIn URL", "social"),
        "google_maps_embed_url": ("https://maps.google.com/?q=Career+Launcher+Ahmedabad", "url", "Google Maps Embed URL", "social"),
        "homepage_meta_title": ("Career Launcher Ahmedabad | CAT, CLAT, IPMAT, CUET Coaching", "text", "Homepage Meta Title", "seo"),
        "homepage_meta_description": (
            "Join Career Launcher Ahmedabad for expert coaching in CAT, CLAT, IPMAT, GMAT, CUET and Class XI-XII Mathematics.",
            "textarea",
            "Homepage Meta Description",
            "seo",
        ),
        "og_image_url": ("https://clahmedabad.onrender.com/static/img/og-default.jpg", "url", "OG Image URL", "seo"),
        "hero_headline": ("Your IIM and NLU Dream Starts Here", "text", "Hero Headline", "display"),
        "hero_subheadline": (
            "Expert coaching for CAT, CLAT, IPMAT and more with Ahmedabad's trusted mentorship team.",
            "textarea",
            "Hero Subheadline",
            "display",
        ),
        "show_scholarship_banner": ("1", "boolean", "Show Scholarship Banner", "display"),
        "scholarship_banner_text": ("Up to 50% Scholarship Available", "text", "Scholarship Banner Text", "display"),
    }

    for key, (value, setting_type, label, group) in default_settings.items():
        setting = SiteSetting.query.filter_by(key=key).first()
        if not setting:
            setting = SiteSetting(
                key=key,
                value=value,
                setting_type=setting_type,
                label=label,
                group=group,
                updated_by=admin_user.id,
            )
            db.session.add(setting)


def seed_data():
    admin_user = seed_admin_user()
    seed_faculty_data()
    seed_course_data()
    seed_result_data()
    seed_blog_posts(admin_user)
    seed_test_series_data()
    seed_scholarship_questions()
    seed_site_settings(admin_user)

    db.session.commit()
    print('Seed data completed successfully.')


def run():
    seed_data()


if __name__ == '__main__':
    flask_env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(flask_env)
    with app.app_context():
        seed_data()
