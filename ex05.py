"""
PHÂN TÍCH BÀI TOÁN
1. Vì sao cần dùng Pydantic BaseModel thay vì lấy thủ công từng key?
   - Nếu lấy dữ liệu thủ công bằng dict (request["age"], request["email"]...),
     chương trình sẽ không tự kiểm tra kiểu dữ liệu, không tự validate định
     dạng, và dễ bị crash (KeyError, TypeError) khi client gửi thiếu trường
     hoặc gửi sai kiểu dữ liệu.
   - Pydantic BaseModel cho phép khai báo rõ kiểu dữ liệu, ràng buộc
     (min_length, ge, le, max_length...) và FastAPI sẽ tự động validate
     trước khi vào hàm xử lý. Nếu dữ liệu sai, FastAPI tự trả lỗi 422
     mà không làm crash server.

2. Các ràng buộc cần validate và cách triển khai:
   - full_name: không được để trống, tối thiểu 3 ký tự
     -> dùng Field(..., min_length=3).
   - email: phải đúng định dạng email
     -> dùng kiểu EmailStr của Pydantic.
   - age: phải là số nguyên, từ 15 đến 60
     -> dùng kiểu int kèm Field(..., ge=15, le=60).
   - phone: chỉ chứa chữ số, độ dài từ 10 đến 11 số
     -> dùng field_validator để kiểm tra str.isdigit() và độ dài chuỗi,
        vì ràng buộc "chỉ chứa số" không thể khai báo bằng Field thông
        thường mà cần một hàm validate riêng.
   - note: không bắt buộc, nếu có thì tối đa 200 ký tự
     -> dùng Optional[str] = Field(default=None, max_length=200).

3. Xử lý khi dữ liệu hợp lệ / không hợp lệ:
   - Nếu dữ liệu hợp lệ: trả về message thành công kèm data đã chuẩn hóa
     (full_name được loại bỏ khoảng trắng dư, note được chuyển về chữ
     thường), đồng thời sinh thêm registration_code cho học viên (phần
     sáng tạo thêm).
   - Nếu dữ liệu không hợp lệ: FastAPI tự động trả về lỗi 422 Unprocessable
     Entity kèm chi tiết trường nào sai, không cần xử lý thêm thủ công,
     và server không bị crash.
"""

import random
import string
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field, field_validator

app = FastAPI()


class StudentRegister(BaseModel):
    full_name: str = Field(..., min_length=3)
    email: EmailStr
    age: int = Field(..., ge=15, le=60)
    phone: str
    course: str
    note: Optional[str] = Field(default=None, max_length=200)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("phone chỉ được chứa chữ số")
        if not (10 <= len(value) <= 11):
            raise ValueError("phone phải có độ dài từ 10 đến 11 số")
        return value


def generate_registration_code() -> str:
    suffix = "".join(random.choices(string.digits, k=6))
    return f"HV-{suffix}"


@app.post("/students/register")
def register_student(student: StudentRegister):
    normalized_data = {
        "registration_code": generate_registration_code(),
        "full_name": student.full_name.strip(),
        "email": student.email,
        "age": student.age,
        "phone": student.phone,
        "course": student.course,
        "note": student.note.strip().lower() if student.note else None,
    }

    return {
        "message": "Đăng ký học viên thành công",
        "data": normalized_data,
    }