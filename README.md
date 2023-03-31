# Quip to Confluence

Quip의 html 백업을 Confluence로 이사하는 도구

## 사용법

```sh
python main.py --page-id [시작페이지] --input-path [시작디렉토리] --recursive --space-key [프로젝트키]
```

- page-id 컨플루언스에 올리기 시작할 위치의 `pageid`
- input-path 올릴 html 백업 파일들의 최상위 디렉토리
- space-key 컨플루언스 프로젝트의 키. 페이지 좌하단 `공간 도구`에서 `개요`로 들어가면 `공간 세부사항`에서 확인 가능
- recursive 이 옵션이 있으면 하위 디렉토리를 따라가며 올린다

### 예시

```sh
python main.py --page-id 42 --input-path backup --recursive --space-key "MYSPACE"
```
