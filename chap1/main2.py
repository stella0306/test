# import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import time


def gall_id(url:str) -> str:
    # 정규식을 사용하여 쿼리 파라미터에서 'id' 값을 추출
    match = re.search(r'[?&]id=([^&]+)', url.lower())
    
    # 매치가 존재하면 해당 값을 반환하고, 없으면 None을 반환
    return match.group(1) if match else None


def remove_brackets_and_parentheses(text:str) -> str:
    if text is not None:
        # 입력이 문자열이 아닐 경우 문자열로 변환
        text = str(text) if not isinstance(text, str) else text
        
        # 정규식을 사용하여 []와 ()를 제거
        return re.sub(r'[\[\]()]', '', text)
    else:
        return text


def mgallery_parser(source:str):
    soup = BeautifulSoup(markup=source, features="lxml")
    properties = soup.find_all("tr", attrs="ub-content")
    
    for i in properties:
        # 게시글 번호
        document_creation_number = None if (temp := i.find("td", attrs={"class" : "gall_num"})) is None else temp.get_text(strip=True)

        # 게시글 토픽
        subject_inner_check = i.find("p", attrs={"class" : "subject_inner"})
        if subject_inner_check:
            document_topic = None if (temp := subject_inner_check) is None else temp.get_text(strip=True)
        
        else:
            document_topic = None if (temp := i.find("td", attrs={"class" : "gall_subject"})) is None else temp.get_text(strip=True)

        # 게시글 이름
        document_title = None if (temp := i.find("a")) is None else temp.get_text(strip=True)
        # 게시글 댓글 수
        document_comment_count = 0 if (temp := i.find("span", attrs={"class": "reply_num"})) is None else temp.get_text(strip=True)
        # 사용자 이름
        document_user = None if (temp := i.find("span", attrs={"class": "nickname"})) is None else temp.get_text(strip=True)
        # 사용자 식별코드
        temp_id = i.find("td", attrs={"class": "gall_writer ub-writer"})
        document_user_code = temp_id.get("data-uid") if temp_id and temp_id.get("data-uid") and len(temp_id.get("data-uid").strip()) != 0 else None
        # 사용자 IP
        document_user_ip = None if (temp := i.find("span", attrs={"class": "ip"})) is None else temp.get_text(strip=True)
        # 게시글 작성일
        document_date = None if (temp := i.find("td", attrs={"class": "gall_date"})) is None else temp.get_text(strip=True)
        # 게시글 조회수
        document_view_count = None if (temp := i.find("td", attrs={"class": "gall_count"})) is None else temp.get_text(strip=True)
        # 게시글 추천 수
        document_recommend_count = None if (temp := i.find("td", attrs={"class": "gall_recommend"})) is None else temp.get_text(strip=True)
        # 게시글 URL
        document_url = None if (temp := i.find("a")) is None else "https://gall.dcinside.com/" + str(gall_id(temp["href"])) + "/" + str(document_creation_number)

        yield {
            "document creation number": document_creation_number,
            "document topic": document_topic,
            "document title": document_title,
            "document comment count": remove_brackets_and_parentheses(text=document_comment_count),
            "document user": document_user,
            "document user code": document_user_code,
            "document user ip": remove_brackets_and_parentheses(text=document_user_ip),
            "document date": document_date,
            "document view count": document_view_count,
            "document recommend count": document_recommend_count,
            "document url": document_url,
        }


async def fetch(session:object, url:str, payload:dict, headers:dict) -> str:
    async with session.get(url, params=payload, headers=headers, timeout=10) as response:
        # 응답 상태 코드 처리
        if response.status == 200:
            return await response.text(encoding="utf-8")  # 성공적으로 응답을 받은 경우
        
        # 재시도할 상태 코드 리스트
        retry_statuses = {429, 500, 503}
        
        if response.status in retry_statuses:
            print(f"Received {response.status} error, waiting for 5 seconds before retrying...")
            await asyncio.sleep(5)  # 재시도 전에 5초 대기
            return await fetch(session=session, url=url, payload=payload, headers=headers)  # 재귀적으로 요청 재시도
        
        # 기타 오류 상태에 대한 처리
        print(f"Error: Received status code {response.status} for URL: {url}")
        print(f"Error: Received status code {response.status} for PAYLOAD: {payload}")
        return None  # 오류 상태일 경우 None 반환


async def mgallery_scraper(url:str, headers:dict, payload:dict) -> None:
    async with aiohttp.ClientSession() as session:
        for page in range(1, 9999999):
            payload["page"] = page
            response_text = await fetch(session=session, url=url, payload=payload, headers=headers)

            if response_text is None:
                raise ValueError("response is none")
            
            for index, data in enumerate(mgallery_parser(source=response_text), start=1):
                for key, value in data.items():
                    print(key, ":", value)
                
                print(f"current page: {page}, current index: {index}\n")

            if (data["document user"] is None) and (data["document user ip"] is None) and (data["document user code"] is None):
                print("마지막 페이지로 판단됨.")
                break

            await asyncio.sleep(1)  # 비동기적으로 1초 대기


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "DNT": "1",
    "Host": "gall.dcinside.com",
    "Referer": "https://www.dcinside.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}

url = "https://gall.dcinside.com/mgallery/board/lists/"

payload = {
    "id": "vanced",
    "list_num": "100",
    "sort_type": "N",
    "search_head": "",
    "page": "",
}


# 비동기 이벤트 루프 실행
asyncio.run(mgallery_scraper(url=url, headers=headers, payload=payload))