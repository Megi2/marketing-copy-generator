// 문구 생성 폼 제출
document.getElementById('generate-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    // 빈 값 제거
    Object.keys(data).forEach(key => {
        if (!data[key]) delete data[key];
    });
    
    // 숫자 타입 변환
    if (data.count) data.count = parseInt(data.count);
    
    // 버튼 비활성화
    const btn = e.target.querySelector('.btn-generate');
    btn.disabled = true;
    btn.textContent = '생성 중...';
    
    // 결과 영역 표시
    const resultSection = document.getElementById('result-section');
    resultSection.style.display = 'block';
    
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading">🤖 AI가 문구를 생성하고 있습니다...</div>';
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result.copies);
        } else {
            resultsDiv.innerHTML = `<div style="color: red;">오류: ${result.error}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div style="color: red;">오류: ${error.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '✨ 문구 생성하기';
    }
});

// 결과 표시 함수
function displayResults(copies) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';
    
    copies.forEach((copy, index) => {
        const div = document.createElement('div');
        div.className = 'copy-item';
        
        // 앱푸시인 경우 타이틀과 본문을 구분하여 표시
        if (copy.title && copy.message) {
            div.innerHTML = `
                <div class="copy-text">
                    <div class="copy-title"><strong>타이틀:</strong> ${copy.title}</div>
                    <div class="copy-message"><strong>본문:</strong> ${copy.message}</div>
                </div>
                <button class="btn-copy" onclick="copyToClipboard('타이틀: ${copy.title}\\n본문: ${copy.message}')">
                    📋 복사
                </button>
            `;
        } else if (copy.message && copy.message.includes('타이틀:')) {
            // "타이틀: ..." 형식의 문자열을 파싱
            const messageText = copy.message;
            const titleMatch = messageText.match(/타이틀:\s*(.+)/);
            const bodyMatch = messageText.match(/본문:\s*(.+)/);
            
            if (titleMatch) {
                const title = titleMatch[1].trim();
                const body = bodyMatch ? bodyMatch[1].trim() : '(광고) ' + title;
                
                div.innerHTML = `
                    <div class="copy-text">
                        <div class="copy-title"><strong>타이틀:</strong> ${title}</div>
                        <div class="copy-message"><strong>본문:</strong> ${body}</div>
                    </div>
                    <button class="btn-copy" onclick="copyToClipboard('타이틀: ${title}\\n본문: ${body}')">
                        📋 복사
                    </button>
                `;
            } else {
                // 파싱 실패 시 기존 방식
                const copyText = copy.message || copy;
                div.innerHTML = `
                    <span class="copy-text">${index + 1}. ${copyText}</span>
                    <button class="btn-copy" onclick="copyToClipboard('${copyText.replace(/'/g, "\\'")}')">
                        📋 복사
                    </button>
                `;
            }
        } else {
            // RCS인 경우 버튼과 메시지 분리 표시
            const button = copy.button || '';
            const message = (copy.message || copy).replace(/\\n/g, '\n'); // 줄바꿈 변환
            
            const messageHtml = message.replace(/\n/g, '<br>'); // HTML 줄바꿈으로 변환
            
            div.innerHTML = `
                <div class="rcs-copy">
                    <div class="rcs-button">${index + 1}. <strong>버튼:</strong> ${button}</div>
                    <div class="rcs-message"><strong>메시지:</strong><br>${messageHtml}</div>
                </div>
                <button class="btn-copy" onclick="copyToClipboard('버튼: ${button}\\n메시지: ${message.replace(/\n/g, '\\n')}')">
                    📋 복사
                </button>
            `;
        }
        
        resultsDiv.appendChild(div);
    });
}

// 클립보드 복사 함수
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('📋 클립보드에 복사되었습니다!');
    }).catch(err => {
        console.error('복사 실패:', err);
    });
}

// 트렌드 조회 함수 (archive.html에서 사용)
async function loadTrends() {
    try {
        const response = await fetch('/api/trends?limit=10');
        const result = await response.json();
        
        if (result.success) {
            displayTrends(result.trends);
        }
    } catch (error) {
        console.error('트렌드 로드 실패:', error);
    }
}

function displayTrends(trends) {
    const container = document.getElementById('trends-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    trends.forEach(trend => {
        const div = document.createElement('div');
        div.className = 'trend-item';
        div.innerHTML = `
            <div class="trend-keyword">${trend.keyword}</div>
            <div class="trend-info">
                <span class="trend-category">${trend.category}</span>
                <span class="trend-score">점수: ${trend.trend_score}</span>
                <span class="trend-mentions">언급: ${trend.mention_count}</span>
            </div>
        `;
        container.appendChild(div);
    });
}

// 팀 아카이브 조회
async function loadArchive(teamId) {
    try {
        const response = await fetch(`/api/archive?team_id=${teamId}`);
        const result = await response.json();
        
        if (result.success) {
            displayArchive(result.copies);
        }
    } catch (error) {
        console.error('아카이브 로드 실패:', error);
    }
}

function displayArchive(copies) {
    const container = document.getElementById('archive-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    copies.forEach(copy => {
        const div = document.createElement('div');
        div.className = 'archive-item';
        div.innerHTML = `
            <div class="archive-text">${copy.copy_text}</div>
            <div class="archive-meta">
                <span>타겟: ${copy.target_audience || 'N/A'}</span>
                <span>톤: ${copy.tone || 'N/A'}</span>
                <span>성과: ${copy.performance_score || 0}</span>
            </div>
        `;
        container.appendChild(div);
    });
}