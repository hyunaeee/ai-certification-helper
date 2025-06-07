import PyPDF2
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import json

@dataclass
class Question:
    """문제 데이터 구조"""
    question_number: int
    question_text: str
    options: List[str]
    answer: Optional[str] = None
    explanation: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None

class CertificationPDFChunker:
    def __init__(self):
        # 문제 번호 패턴 (1., 2., 3. 또는 1) 2) 3) 형태)
        self.question_pattern = re.compile(r'^(\d+)[.)]\s*(.+?)$', re.MULTILINE | re.DOTALL)
        # 선택지 패턴 (①, ②, ③, ④ 또는 1), 2), 3), 4) 형태)
        self.option_patterns = [
            re.compile(r'[①②③④⑤]'),  # 원문자
            re.compile(r'[1-5][)]'),   # 숫자+괄호
            re.compile(r'[가-마][)]'), # 한글+괄호
            re.compile(r'[A-E][)]'),   # 영문+괄호
        ]
        # 정답 패턴
        self.answer_pattern = re.compile(r'정답[:\s]*([①②③④⑤1-5가-마A-E])')
        # 해설 패턴
        self.explanation_pattern = re.compile(r'(?:해설|설명)[:\s]*(.+?)(?=\n\d+[.)]|\n정답|\Z)', re.DOTALL)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"PDF 읽기 오류: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        # 페이지 번호 제거
        text = re.sub(r'페이지\s*\d+', '', text)
        # 헤더/푸터 패턴 제거
        text = re.sub(r'제\d+회.*?기출문제', '', text)
        return text.strip()

    def detect_option_pattern(self, text: str) -> Optional[re.Pattern]:
        """선택지 패턴 감지"""
        for pattern in self.option_patterns:
            if len(pattern.findall(text)) >= 2:  # 최소 2개 이상의 선택지가 있어야 함
                return pattern
        return None

    def extract_options(self, text: str, option_pattern: re.Pattern) -> List[str]:
        """선택지 추출"""
        if not option_pattern:
            return []
        
        # 선택지 분리
        parts = option_pattern.split(text)
        options = []
        
        for i in range(1, len(parts)):
            option_text = parts[i].strip()
            # 다음 문제나 정답 부분까지만 추출
            option_text = re.split(r'\n\d+[.)]|\n정답', option_text)[0].strip()
            if option_text:
                options.append(option_text)
        
        return options

    def extract_answer(self, text: str) -> Optional[str]:
        """정답 추출"""
        match = self.answer_pattern.search(text)
        return match.group(1) if match else None

    def extract_explanation(self, text: str) -> Optional[str]:
        """해설 추출"""
        match = self.explanation_pattern.search(text)
        return match.group(1).strip() if match else None

    def categorize_question(self, question_text: str) -> str:
        """문제 카테고리 분류 (키워드 기반)"""
        keywords_map = {
            "프로그래밍": ["코드", "프로그램", "함수", "변수", "알고리즘", "Java", "Python", "C++"],
            "데이터베이스": ["SQL", "데이터베이스", "테이블", "쿼리", "관계형"],
            "네트워크": ["네트워크", "TCP", "IP", "OSI", "프로토콜", "라우터"],
            "보안": ["보안", "암호화", "해킹", "인증", "방화벽"],
            "시스템": ["운영체제", "OS", "메모리", "프로세스", "스케줄링"],
            "소프트웨어공학": ["설계", "모델링", "UML", "요구사항", "테스트"]
        }
        
        for category, keywords in keywords_map.items():
            if any(keyword in question_text for keyword in keywords):
                return category
        return "기타"

    def estimate_difficulty(self, question_text: str, options: List[str]) -> str:
        """문제 난이도 추정"""
        # 간단한 난이도 추정 로직
        complexity_indicators = ["구현", "설계", "분석", "평가", "비교"]
        
        if len(options) > 4:
            return "상"
        elif any(indicator in question_text for indicator in complexity_indicators):
            return "중"
        else:
            return "하"

    def chunk_pdf(self, pdf_path: str) -> List[Question]:
        """PDF를 문제별로 청킹"""
        # PDF에서 텍스트 추출
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text:
            return []

        # 텍스트 정리
        clean_text = self.clean_text(raw_text)
        
        # 문제별로 분할
        question_blocks = self.question_pattern.split(clean_text)
        questions = []
        
        # 선택지 패턴 감지
        option_pattern = self.detect_option_pattern(clean_text)
        
        for i in range(1, len(question_blocks), 2):
            try:
                question_num = int(question_blocks[i])
                question_content = question_blocks[i + 1] if i + 1 < len(question_blocks) else ""
                
                # 문제 텍스트와 선택지 분리
                question_parts = question_content.split('\n')
                question_text = question_parts[0].strip()
                
                # 선택지 추출
                options = self.extract_options(question_content, option_pattern)
                
                # 정답 추출
                answer = self.extract_answer(question_content)
                
                # 해설 추출
                explanation = self.extract_explanation(question_content)
                
                # 카테고리 및 난이도 분류
                category = self.categorize_question(question_text)
                difficulty = self.estimate_difficulty(question_text, options)
                
                question = Question(
                    question_number=question_num,
                    question_text=question_text,
                    options=options,
                    answer=answer,
                    explanation=explanation,
                    category=category,
                    difficulty=difficulty
                )
                
                questions.append(question)
                
            except (ValueError, IndexError) as e:
                print(f"문제 {i//2 + 1} 처리 중 오류: {e}")
                continue
        
        return questions

    def save_to_json(self, questions: List[Question], output_path: str):
        """JSON 파일로 저장"""
        data = []
        for q in questions:
            data.append({
                "question_number": q.question_number,
                "question_text": q.question_text,
                "options": q.options,
                "answer": q.answer,
                "explanation": q.explanation,
                "category": q.category,
                "difficulty": q.difficulty
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_statistics(self, questions: List[Question]) -> Dict:
        """문제 통계 정보"""
        total = len(questions)
        categories = {}
        difficulties = {}
        
        for q in questions:
            categories[q.category] = categories.get(q.category, 0) + 1
            difficulties[q.difficulty] = difficulties.get(q.difficulty, 0) + 1
        
        return {
            "total_questions": total,
            "categories": categories,
            "difficulties": difficulties
        }

# 사용 예시
if __name__ == "__main__":
    chunker = CertificationPDFChunker()
    
    # PDF 청킹
    pdf_path = "기출문제.pdf"
    questions = chunker.chunk_pdf(pdf_path)
    
    # 결과 저장
    chunker.save_to_json(questions, "questions.json")
    
    # 통계 출력
    stats = chunker.get_statistics(questions)
    print(f"총 문제 수: {stats['total_questions']}")
    print(f"카테고리별: {stats['categories']}")
    print(f"난이도별: {stats['difficulties']}")
    
    # 샘플 문제 출력
    if questions:
        print(f"\n샘플 문제:")
        q = questions[0]
        print(f"문제 {q.question_number}: {q.question_text}")
        for i, option in enumerate(q.options, 1):
            print(f"  {i}) {option}")
        print(f"정답: {q.answer}")
        print(f"카테고리: {q.category}, 난이도: {q.difficulty}")
