"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import inspect
import json
from typing import Any, Dict, Optional

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập"
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"]
        }
    },
    {
        "name": "list_appointments",
        "description": "Liệt kê các lịch hẹn tư vấn học vụ của một sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần xem lịch hẹn (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "cancel_appointment",
        "description": "Hủy một lịch hẹn tư vấn học vụ theo mã đặt lịch.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên sở hữu lịch hẹn"
                },
                "booking_id": {
                    "type": "string",
                    "description": "Mã đặt lịch cần hủy (ví dụ: 'BK-SV2026001-01')"
                }
            },
            "required": ["student_id", "booking_id"]
        }
    },
    {
        "name": "exam_schedule_query",
        "description": "Tra cứu lịch thi theo mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu lịch thi"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "tuition_query",
        "description": "Tra cứu học phí và tình trạng thanh toán của sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu học phí"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "course_search",
        "description": "Tìm môn học trong danh mục VinUni theo mã môn hoặc từ khóa tên môn.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Mã môn hoặc từ khóa (ví dụ: 'AI301' hoặc 'Machine Learning')"
                }
            },
            "required": ["keyword"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU JSON KHỚP THAM SỐ SCHEMA
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "student_id": "SV2026001",
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A",
        "credits_earned": 96
    },
    "SV2026002": {
        "student_id": "SV2026002",
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B",
        "credits_earned": 88
    },
    "SV2026003": {
        "student_id": "SV2026003",
        "full_name": "Lê Văn Cường",
        "class": "AI-K4",
        "gpa": 3.42,
        "email": "cuong.lv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A",
        "credits_earned": 72
    }
}

MOCK_APPOINTMENTS = [
    {
        "booking_id": "BK-SV2026001-01",
        "student_id": "SV2026001",
        "datetime_str": "09:00 10/09/2026",
        "advisor_name": "PGS.TS Nguyễn Văn A",
        "topic": "Tư vấn lộ trình học tập",
        "status": "CONFIRMED"
    },
    {
        "booking_id": "BK-SV2026002-01",
        "student_id": "SV2026002",
        "datetime_str": "14:00 12/09/2026",
        "advisor_name": "TS. Lê Thị B",
        "topic": "Tư vấn cải thiện GPA",
        "status": "CONFIRMED"
    }
]

MOCK_EXAMS = {
    "SV2026001": [
        {
            "student_id": "SV2026001",
            "course_code": "AI301",
            "course_name": "Machine Learning",
            "datetime_str": "08:00 20/10/2026",
            "room": "C201"
        },
        {
            "student_id": "SV2026001",
            "course_code": "AI305",
            "course_name": "Natural Language Processing",
            "datetime_str": "13:30 22/10/2026",
            "room": "B105"
        }
    ],
    "SV2026002": [
        {
            "student_id": "SV2026002",
            "course_code": "AI301",
            "course_name": "Machine Learning",
            "datetime_str": "08:00 20/10/2026",
            "room": "C201"
        }
    ],
    "SV2026003": [
        {
            "student_id": "SV2026003",
            "course_code": "CS201",
            "course_name": "Data Structures",
            "datetime_str": "09:00 18/10/2026",
            "room": "A203"
        }
    ]
}

MOCK_TUITION = {
    "SV2026001": {
        "student_id": "SV2026001",
        "semester": "2026-1",
        "amount_vnd": 45000000,
        "paid_vnd": 45000000,
        "status": "PAID"
    },
    "SV2026002": {
        "student_id": "SV2026002",
        "semester": "2026-1",
        "amount_vnd": 45000000,
        "paid_vnd": 20000000,
        "status": "PARTIAL"
    },
    "SV2026003": {
        "student_id": "SV2026003",
        "semester": "2026-1",
        "amount_vnd": 45000000,
        "paid_vnd": 0,
        "status": "UNPAID"
    }
}

MOCK_COURSES = [
    {
        "course_code": "AI301",
        "course_name": "Machine Learning",
        "credits": 3,
        "instructor": "PGS.TS Nguyễn Văn A",
        "keyword": "machine learning ai"
    },
    {
        "course_code": "AI305",
        "course_name": "Natural Language Processing",
        "credits": 3,
        "instructor": "TS. Lê Thị B",
        "keyword": "nlp language"
    },
    {
        "course_code": "CS201",
        "course_name": "Data Structures",
        "credits": 4,
        "instructor": "TS. Phạm Quốc Dũng",
        "keyword": "data structures algorithms"
    }
]


def _dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _find_student(student_id: str) -> Optional[Dict[str, Any]]:
    return MOCK_DATABASE.get((student_id or "").strip().upper())


def _student_not_found(student_id: str, action: str) -> str:
    return _dumps({
        "status": "NOT_FOUND",
        "message": f"Không thể {action} vì không tìm thấy sinh viên có mã '{student_id}'"
    })


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên (tham số schema: student_id)."""
    student = _find_student(student_id)
    if student:
        return _dumps({
            "status": "SUCCESS",
            "student_id": student["student_id"],
            "data": student
        })
    return _dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
    })


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str) -> str:
    """Thực thi đặt lịch hẹn (tham số schema: student_id, datetime_str, advisor_name)."""
    student = _find_student(student_id)
    if not student:
        return _student_not_found(student_id, "đặt lịch")

    booking = {
        "booking_id": f"BK-{student['student_id']}-{len(MOCK_APPOINTMENTS) + 1:02d}",
        "student_id": student["student_id"],
        "datetime_str": datetime_str,
        "advisor_name": advisor_name,
        "student_name": student["full_name"],
        "status": "CONFIRMED"
    }
    MOCK_APPOINTMENTS.append(booking)

    return _dumps({
        "status": "SUCCESS",
        "booking_id": booking["booking_id"],
        "student_id": booking["student_id"],
        "datetime_str": booking["datetime_str"],
        "advisor_name": booking["advisor_name"],
        "datetime": booking["datetime_str"],
        "advisor": booking["advisor_name"],
        "message": (
            f"Đặt lịch thành công cho sinh viên {booking['student_id']} "
            f"({student['full_name']}) với {booking['advisor_name']} "
            f"vào lúc {booking['datetime_str']}."
        )
    })


def execute_list_appointments(student_id: str) -> str:
    """Liệt kê lịch hẹn theo student_id."""
    student = _find_student(student_id)
    if not student:
        return _student_not_found(student_id, "xem lịch hẹn")

    items = [
        item for item in MOCK_APPOINTMENTS
        if item["student_id"] == student["student_id"]
    ]
    return _dumps({
        "status": "SUCCESS",
        "student_id": student["student_id"],
        "count": len(items),
        "data": items,
        "message": (
            f"Sinh viên {student['student_id']} có {len(items)} lịch hẹn."
            if items else
            f"Sinh viên {student['student_id']} chưa có lịch hẹn nào."
        )
    })


def execute_cancel_appointment(student_id: str, booking_id: str) -> str:
    """Hủy lịch hẹn theo student_id + booking_id."""
    student = _find_student(student_id)
    if not student:
        return _student_not_found(student_id, "hủy lịch")

    booking_id = (booking_id or "").strip()
    for item in MOCK_APPOINTMENTS:
        if item["booking_id"] == booking_id and item["student_id"] == student["student_id"]:
            if item["status"] == "CANCELLED":
                return _dumps({
                    "status": "SUCCESS",
                    "student_id": student["student_id"],
                    "booking_id": booking_id,
                    "message": f"Lịch hẹn {booking_id} đã được hủy trước đó."
                })
            item["status"] = "CANCELLED"
            return _dumps({
                "status": "SUCCESS",
                "student_id": student["student_id"],
                "booking_id": booking_id,
                "datetime_str": item["datetime_str"],
                "advisor_name": item["advisor_name"],
                "message": (
                    f"Đã hủy lịch hẹn {booking_id} của sinh viên {student['student_id']} "
                    f"với {item['advisor_name']} lúc {item['datetime_str']}."
                )
            })

    return _dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy lịch hẹn '{booking_id}' của sinh viên '{student_id}'."
    })


def execute_exam_schedule_query(student_id: str) -> str:
    """Tra cứu lịch thi theo student_id."""
    student = _find_student(student_id)
    if not student:
        return _student_not_found(student_id, "tra cứu lịch thi")

    exams = MOCK_EXAMS.get(student["student_id"], [])
    return _dumps({
        "status": "SUCCESS",
        "student_id": student["student_id"],
        "count": len(exams),
        "data": exams,
        "message": (
            f"Sinh viên {student['student_id']} có {len(exams)} ca thi."
            if exams else
            f"Chưa có lịch thi cho sinh viên {student['student_id']}."
        )
    })


def execute_tuition_query(student_id: str) -> str:
    """Tra cứu học phí theo student_id."""
    student = _find_student(student_id)
    if not student:
        return _student_not_found(student_id, "tra cứu học phí")

    record = MOCK_TUITION.get(student["student_id"])
    if not record:
        return _dumps({
            "status": "NOT_FOUND",
            "message": f"Chưa có dữ liệu học phí cho sinh viên '{student_id}'."
        })

    remaining = record["amount_vnd"] - record["paid_vnd"]
    return _dumps({
        "status": "SUCCESS",
        "student_id": student["student_id"],
        "data": record,
        "message": (
            f"Học phí {record['semester']} của {student['student_id']}: "
            f"{record['amount_vnd']:,} VND, đã đóng {record['paid_vnd']:,} VND, "
            f"còn lại {remaining:,} VND ({record['status']})."
        )
    })


def execute_course_search(keyword: str) -> str:
    """Tìm môn học theo keyword (mã môn hoặc tên)."""
    needle = (keyword or "").strip().lower()
    if not needle:
        return _dumps({
            "status": "EXECUTION_ERROR",
            "error": "Thiếu từ khóa tìm môn học."
        })

    matches = []
    for course in MOCK_COURSES:
        blob = f"{course['course_code']} {course['course_name']} {course.get('keyword', '')}".lower()
        if needle in blob:
            matches.append({k: v for k, v in course.items() if k != "keyword"})

    if not matches:
        return _dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy môn học khớp với từ khóa '{keyword}'."
        })

    return _dumps({
        "status": "SUCCESS",
        "keyword": keyword,
        "count": len(matches),
        "data": matches,
        "message": f"Tìm thấy {len(matches)} môn học khớp với '{keyword}'."
    })


TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "list_appointments": execute_list_appointments,
    "cancel_appointment": execute_cancel_appointment,
    "exam_schedule_query": execute_exam_schedule_query,
    "tuition_query": execute_tuition_query,
    "course_search": execute_course_search
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            func = TOOL_ROUTER[tool_name]
            params = inspect.signature(func).parameters
            filtered = {k: v for k, v in (arguments or {}).items() if k in params}
            return func(**filtered)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
