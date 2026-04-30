# WPMT Brand Vault — 셋업 가이드

윔프매터 브랜드 운영용 보관함. **기존 `bookmark-vault` 와 데이터 100% 분리**됨.

## 0. 차이점 한눈에

| 항목 | bookmark-vault (기존) | WPMT-brand-vault (이거) |
|---|---|---|
| Supabase 테이블 | `bv_data` | `wpmt_brand_vault` |
| 카테고리 | 인플 / 정보 / 쇼핑 등 | 이미지 프롬프트 / 콘텐츠 아이디어 / 관련 서비스 / 굿즈 / AI ETC |
| 파일 보관 | 없음 | Google Drive (`WPMT-Brand-Vault` 폴더 자동 생성) |
| 랜덤 뽑기 | 없음 | 홈에서 이미지/영상 랜덤 |
| 배포 | 별도 URL | 별도 URL |

→ 한 Supabase 프로젝트 안에서 **테이블만 분리**됐기 때문에 어느 한쪽이 다른 쪽을 절대 덮어쓸 수 없어.

---

## 1. Supabase 테이블 생성 (1분)

[Supabase 대시보드](https://supabase.com/dashboard/project/ksuiqtlrcenzedtlxyrb/sql/new) 열고 아래 SQL 실행:

```sql
-- 1) 테이블
create table if not exists public.wpmt_brand_vault (
  user_id uuid primary key references auth.users(id) on delete cascade,
  bookmarks jsonb not null default '[]'::jsonb,
  drive_folder_id text,
  updated_at timestamptz default now()
);

-- 2) RLS 켜기
alter table public.wpmt_brand_vault enable row level security;

-- 3) 정책: 본인 데이터만 읽고 쓰기
create policy "wpmt own select" on public.wpmt_brand_vault
  for select using (auth.uid() = user_id);

create policy "wpmt own insert" on public.wpmt_brand_vault
  for insert with check (auth.uid() = user_id);

create policy "wpmt own update" on public.wpmt_brand_vault
  for update using (auth.uid() = user_id);

create policy "wpmt own delete" on public.wpmt_brand_vault
  for delete using (auth.uid() = user_id);
```

---

## 2. Google Drive OAuth Client ID 만들기 (5분)

`wimpmatter.studio@gmail.com` 로 진행.

1. [Google Cloud Console](https://console.cloud.google.com/) 접속 → 우상단 계정이 `wimpmatter.studio@gmail.com` 인지 확인
2. 상단 프로젝트 셀렉터 → **새 프로젝트** → 이름: `WPMT Brand Vault` → 만들기
3. 좌측 햄버거 → **API 및 서비스 → 라이브러리** → "Google Drive API" 검색 → **사용** 버튼
4. **API 및 서비스 → OAuth 동의 화면**:
   - User Type: **외부** → 만들기
   - 앱 이름: `WPMT Brand Vault`
   - 사용자 지원 이메일: `wimpmatter.studio@gmail.com`
   - 개발자 연락처: `wimpmatter.studio@gmail.com`
   - 저장 후 계속
5. **범위 추가 또는 삭제** → `https://www.googleapis.com/auth/drive.file` 체크 → 업데이트 → 저장
6. **테스트 사용자** → `wimpmatter.studio@gmail.com` 추가 → 저장
7. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → OAuth 클라이언트 ID**
   - 애플리케이션 유형: **웹 애플리케이션**
   - 이름: `WPMT Brand Vault Web`
   - **승인된 JavaScript 원본**:
     - `http://localhost:8080` (로컬 테스트용)
     - `http://127.0.0.1:8080`
     - 배포 후 Vercel URL 추가 (예: `https://wpmt-brand-vault.vercel.app`)
   - 만들기
8. 표시된 **클라이언트 ID** 복사 (`xxxxxxxx.apps.googleusercontent.com`)
9. 앱 우상단 **Drive 연결** 버튼 클릭 → 클라이언트 ID 붙여넣기 → 저장

> 한 번 저장하면 브라우저 localStorage에 저장돼서 다시 안 물어봄.

---

## 3. 로컬 실행

```bash
cd /Users/taeholee/클로드코드/WPMT-brand-vault
python3 -m http.server 8080
```

브라우저에서 [http://localhost:8080](http://localhost:8080) 열기.

---

## 4. Vercel 배포

```bash
# 1) GitHub repo 생성 후 푸시
gh repo create WPMT-brand-vault --public --source=. --remote=origin --push

# 2) Vercel 연결 (대시보드에서)
#    https://vercel.com/new → GitHub 리포 import → Deploy
```

배포되면 받은 URL을 Google OAuth 동의 화면 **승인된 JavaScript 원본**에 추가.

---

## 5. 사용법

- **북마크 추가**: 홈 상단 URL 입력 → 카테고리 선택 → 추가
  - 인스타/유튜브/틱톡은 oEmbed로 제목 자동 추출
  - 카드 제목/비고는 클릭해서 직접 수정 가능
- **파일 업로드**: 홈 가운데 박스에 드래그 또는 클릭 → Drive `WPMT-Brand-Vault` 폴더에 저장
- **랜덤 뽑기**: 홈 우측 → 전체/이미지/영상 선택 → 🎲 뽑기 → 클릭하면 큰 화면 미리보기
- **다운로더**: IG/YT URL 카드의 다운로드 버튼 → 기존 instagram-downloader / youtube-downloader 서버 호출

---

## 트러블슈팅

**Drive 인증 후 화면 그대로**: 팝업이 차단되었을 수 있음. 주소창 우측 팝업 차단 해제.

**썸네일 안 보임**: Drive 썸네일은 권한 토큰 필요. 새로고침으로 재요청.

**오디오 떼고 싶음**: 랜덤 뽑기 영상은 `muted` 자동 적용. 미리보기 모달은 사운드 ON.
