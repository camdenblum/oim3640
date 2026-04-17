"""
data.py
Static data for the Campus Advocacy Toolkit — foundations, resources, and pipeline defaults.
"""

FOUNDATIONS = {
    "busyhead": {
        "id": "busyhead",
        "name": "The Busyhead Project",
        "founder": "Noah Kahan",
        "tagline": "Mental health advocacy through music and community.",
        "mission": (
            "The Busyhead Project uses music and storytelling to break down "
            "the stigma around mental health for young people, connecting students "
            "to local resources and peer communities across the country."
        ),
        "impact_stats": [
            "50+ campus activations nationwide",
            "10,000+ students reached through workshops",
            "Community walls deployed on 3 major tours",
        ],
        "focus": "Mental Health",
        "color": "#C96B3E",
        "light_color": "#FDF0EA",
        "website": "https://www.busyheadproject.com",
    },
    "ally": {
        "id": "ally",
        "name": "The Ally Coalition",
        "founder": "Jack Antonoff & Rachel Antonoff",
        "tagline": "Safe schools and communities for LGBTQ+ youth.",
        "mission": (
            "The Ally Coalition partners with artists and schools to create safer, "
            "more inclusive environments for LGBTQ+ students, providing tools for "
            "GSAs, faculty, and administrators to build affirming campuses."
        ),
        "impact_stats": [
            "700+ schools reached with safe-space materials",
            "Annual benefit concerts raising $1M+ for LGBTQ+ youth",
            "GSA toolkits distributed in all 50 states",
        ],
        "focus": "LGBTQ+ Inclusion & Safety",
        "color": "#6B3EC9",
        "light_color": "#F0EAFD",
        "website": "https://www.theally coalition.com",
    },
    "midwest_princess": {
        "id": "midwest_princess",
        "name": "The Midwest Princess Project",
        "founder": "Chappell Roan",
        "tagline": "Trans visibility, safety, and support in schools.",
        "mission": (
            "The Midwest Princess Project fights for the dignity, safety, and "
            "visibility of transgender and gender-nonconforming students, providing "
            "policy toolkits, healthcare navigation resources, and storytelling platforms."
        ),
        "impact_stats": [
            "Trans-inclusive policy checklists adopted at 200+ schools",
            "Healthcare navigation resources used in 35 states",
            "Day of Visibility events coordinated at 100+ campuses",
        ],
        "focus": "Trans Student Support",
        "color": "#3E8EC9",
        "light_color": "#EAF4FD",
        "website": "#",
    },
    "laufey": {
        "id": "laufey",
        "name": "The Laufey Foundation",
        "founder": "Laufey",
        "tagline": "Expanding access to music education for every student.",
        "mission": (
            "The Laufey Foundation believes that music education is not a privilege "
            "but a right. The foundation funds youth orchestras, instrument lending "
            "programs, and mentorship initiatives that bring classical and jazz music "
            "to students who would otherwise never encounter it."
        ),
        "impact_stats": [
            "500+ instruments lent to students free of charge",
            "Scholarship grants awarded to 300+ young musicians",
            "Youth orchestra programs funded in 12 cities",
        ],
        "focus": "Arts Education & Access",
        "color": "#2C4A7C",
        "light_color": "#EAF0FD",
        "website": "#",
    },
}

RESOURCES = {
    "busyhead": [
        {
            "title": "Mental Health 101 Workshop Guide",
            "description": "A complete classroom facilitation guide for a 60-minute mental health awareness workshop. Includes discussion prompts, activity instructions, and facilitator notes.",
            "audience": "Counselors & Teachers",
            "type": "Workshop Guide",
        },
        {
            "title": "Campus Resource Mapping Template",
            "description": "A structured template helping students identify and map local mental health services, crisis lines, and peer support organizations in their area.",
            "audience": "Counselors & Students",
            "type": "Template",
        },
        {
            "title": "Peer Ambassador Training Outline",
            "description": "A training framework for student volunteers who want to serve as mental health advocates and conversation starters among their peers.",
            "audience": "Student Leaders",
            "type": "Training Outline",
        },
        {
            "title": "Social Media Awareness Kit",
            "description": "Shareable graphics, caption templates, and a content calendar for Mental Health Awareness Month social media campaigns.",
            "audience": "Student Organizations",
            "type": "Digital Kit",
        },
        {
            "title": "Story Sharing Guidelines",
            "description": "Safe messaging guidelines and a structured framework for students who want to share their own mental health journeys in school settings.",
            "audience": "Students & Staff",
            "type": "Guidelines",
        },
        {
            "title": "Community Wall Activation Kit",
            "description": "Instructions for replicating the interactive community wall model used on Noah Kahan's tours — a physical space where students post anonymous messages of support and solidarity.",
            "audience": "Event Coordinators",
            "type": "Event Kit",
        },
    ],
    "ally": [
        {
            "title": "GSA Starter Pack",
            "description": "Everything a school needs to launch or revitalize a Gender & Sexuality Alliance: sample bylaws, meeting structure templates, and a year-one activity calendar.",
            "audience": "Student Leaders & Advisors",
            "type": "Starter Pack",
        },
        {
            "title": "Inclusive Curriculum Add-On Guide",
            "description": "Practical recommendations for teachers in English, History, Health, and Arts classes to integrate LGBTQ+ representation into existing lesson plans without full curriculum overhauls.",
            "audience": "Teachers",
            "type": "Curriculum Guide",
        },
        {
            "title": "Allyship Training Script",
            "description": "A facilitated 90-minute allyship training for faculty or students, including icebreakers, scenario-based discussions, and a commitment pledge.",
            "audience": "Faculty & Staff",
            "type": "Training Script",
        },
        {
            "title": "Campus Climate Survey Template",
            "description": "A validated survey instrument to measure the current safety and inclusion climate for LGBTQ+ students, with scoring guidance and recommended benchmarks.",
            "audience": "Administrators",
            "type": "Survey Template",
        },
        {
            "title": "Advocacy Letter Templates",
            "description": "Pre-written letter templates students can customize and send to their principal, school board, or district office requesting policy improvements for LGBTQ+ students.",
            "audience": "Students",
            "type": "Letter Templates",
        },
        {
            "title": "Safe Space Signage Materials",
            "description": "Print-ready safe space signs, stickers, and window decals for classrooms and offices, with guidance on what safe space designation means in practice.",
            "audience": "Teachers & Staff",
            "type": "Signage Kit",
        },
    ],
    "midwest_princess": [
        {
            "title": "Trans Student Support Resource Guide",
            "description": "A comprehensive guide to the legal rights of transgender students in K-12 and higher education, including Title IX protections, name/pronoun policies, and bathroom access rights.",
            "audience": "Students & Counselors",
            "type": "Resource Guide",
        },
        {
            "title": "Trans-Inclusive Policy Checklist",
            "description": "An administrator-facing checklist of 30 policy areas schools should review and update to become truly trans-inclusive, with model policy language for each.",
            "audience": "Administrators",
            "type": "Policy Checklist",
        },
        {
            "title": "Visibility Event Planning Guide",
            "description": "Step-by-step planning guide for Trans Day of Visibility and Trans Awareness Week events, including programming ideas, speaker sourcing, and community partnership strategies.",
            "audience": "Event Coordinators & GSA Advisors",
            "type": "Event Planning Guide",
        },
        {
            "title": "Healthcare Navigation Resource",
            "description": "A curated resource helping trans students locate gender-affirming healthcare providers by region, understand their insurance rights, and navigate campus health services.",
            "audience": "Students & Counselors",
            "type": "Navigation Guide",
        },
        {
            "title": "Student Storytelling Campaign Kit",
            "description": "A structured toolkit for trans students who want to share their stories with their school community safely, including consent forms, editorial guidelines, and publishing templates.",
            "audience": "Students",
            "type": "Campaign Kit",
        },
        {
            "title": "Faculty Allyship Pledge Toolkit",
            "description": "A formal pledge framework for faculty who want to publicly commit to being affirming allies, including pledge language, classroom commitment cards, and professional development resources.",
            "audience": "Faculty",
            "type": "Pledge Toolkit",
        },
    ],
    "laufey": [
        {
            "title": "Youth Orchestra Program Finder",
            "description": "A searchable regional directory of youth orchestra programs, summer music institutes, and conservatory preparatory programs with scholarship and financial aid information.",
            "audience": "Students & Parents",
            "type": "Directory",
        },
        {
            "title": "Instrument Lending Program Setup Guide",
            "description": "A complete operational guide for schools or districts that want to launch an instrument lending program, including inventory management, loan agreements, and maintenance schedules.",
            "audience": "Administrators & Music Directors",
            "type": "Operations Guide",
        },
        {
            "title": "Music Scholarship Application Guide",
            "description": "A step-by-step guide walking students through the Laufey Foundation grant application process, with tips on audition recordings, essays, and letters of recommendation.",
            "audience": "Students",
            "type": "Application Guide",
        },
        {
            "title": "Jazz and Classical Workshop Curriculum",
            "description": "A four-session introductory workshop curriculum designed to introduce students with no prior classical or jazz exposure to the history, theory, and appreciation of both genres.",
            "audience": "Music Teachers",
            "type": "Curriculum",
        },
        {
            "title": "Artist Mentorship Program Framework",
            "description": "A structured framework for connecting student musicians with professional mentors, including matching criteria, session guides, progress tracking, and program evaluation tools.",
            "audience": "Music Directors & Administrators",
            "type": "Program Framework",
        },
        {
            "title": "Campus Concert Series Template",
            "description": "A complete operational template for student-run concert series, including event planning checklists, ticketing models, fundraising strategies, and sponsorship outreach scripts.",
            "audience": "Student Organizations",
            "type": "Event Template",
        },
    ],
}

PIPELINE_STATUSES = ["Contacted", "Responding", "Active Partner", "On Hold"]

FOUNDATION_CHOICES = [
    ("busyhead", "The Busyhead Project"),
    ("ally", "The Ally Coalition"),
    ("midwest_princess", "The Midwest Princess Project"),
    ("laufey", "The Laufey Foundation"),
]

SCHOOL_TYPES = [
    "Public High School",
    "Private High School",
    "Community College",
    "4-Year University",
    "Charter School",
    "Other",
]
