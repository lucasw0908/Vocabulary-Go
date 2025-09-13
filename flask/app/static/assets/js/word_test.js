import $ from 'jquery';

$(function () {
    let jsonData = [];
    let currentQuestion = 0;
    let correctCount = 0;
    let wrongCount = 0;
    let usedIndices = [];
    let currentIndex;
    let mode = 0; // 0: first & last char, 1: only first, 2: none

    const hintWhiteList = ["n", "ving", "v", "vt", "vi", "adj", "adv", "...", "sb", "sth", "one's"];

    const checkButtonElem = document.getElementById('check-button');
    let originalCheckButtonHTML = checkButtonElem.innerHTML;
    const slider = document.getElementById('resize-slider');
    const questionContainer = document.getElementById('question-container');



    function getRandomIndex() {
        if (usedIndices.length >= jsonData.length) return null;
        let randomIndex;
        do {
            randomIndex = Math.floor(Math.random() * jsonData.length);
        } while (usedIndices.includes(randomIndex));
        return randomIndex;
    }

    function formatHint(part) {
        const lowerPart = part.toLowerCase();
        if (hintWhiteList.includes(lowerPart)) return part;
        if (part.length <= 3) return "_";
        const first = part[0], last = part[part.length - 1];
        if (mode === 0) return `${first}_${last}`;
        if (mode === 1) return `${first}_`;
        return "_";
    }

    function getHint() {
        return jsonData[currentIndex].English.split(" ").map(word => {
            const parts = word.split("/");
            if (parts.length > 1) {
                return parts.map(part => formatHint(part)).join(" / ");
            } else {
                return formatHint(word);
            }
        }).join(" ");
    }

    function normalizeAnswer(str) {
        return str
            .split(" ")
            .filter(word => !hintWhiteList.includes(word.toLowerCase()))
            .map(word => {
                if (word.includes("/")) {
                    return word.split("/").sort().join("/");
                }
                return word;
            }).join(" ");
    }

    function loadQuestion() {
        if (currentIndex === null) return;
        document.getElementById('current-question').textContent = currentQuestion;
        document.getElementById('chinese-word').innerHTML =
            `<span id="darken">${getHint()}</span> <span>${jsonData[currentIndex].Chinese}</span>`;
        updateProgressChart();
    }

    function checkAnswer() {
        if (usedIndices.length >= jsonData.length) return;
        const input = document.getElementById('user-input').value.trim().toLowerCase();
        const answer = jsonData[currentIndex].English.toLowerCase();
        const resultElem = document.getElementById('result');
        const nextBtn = document.getElementById('next-button');
        const normalizedInput = normalizeAnswer(input);
        const normalizedAnswer = normalizeAnswer(answer);

        if (normalizedInput === normalizedAnswer) {
            resultElem.textContent = '正確！';
            usedIndices.push(currentIndex);
            correctCount++;
        } else {
            resultElem.textContent = `錯誤，正確答案是: ${answer}`;
            wrongCount++;
        }

        currentQuestion++;
        nextBtn.style.display = 'flex';
        checkButtonElem.style.display = 'none';
        document.getElementById('correct-count').textContent = correctCount;
        document.getElementById('wrong-count').textContent = wrongCount;
        updateProgressChart();
        storeProgress();

        if (usedIndices.length === jsonData.length) {
            document.getElementById('result2').textContent = '已完成作答！';
            const nextButton = document.getElementById('next-button');

            nextButton.style.display = 'none';
            const checkElement = document.getElementById('check-button');
            checkElement.style.display = 'flex';
            changeCheckButtonToReset();
        }
    }
    window.checkAnswer = checkAnswer;

    function nextQuestion() {

        if (usedIndices.length === jsonData.length) return;
        storeProgress();
        document.getElementById('next-button').style.display = 'none';

        checkButtonElem.style.display = 'flex';
        document.getElementById('user-input').value = '';
        document.getElementById('result').textContent = '';
        document.getElementById('result2').textContent = '';
        currentIndex = getRandomIndex();
        if (currentIndex !== null) loadQuestion();
    }

    function changeCheckButtonToReset() {
        const btn = document.getElementById('check-button');
        btn.innerHTML = `
      <span class="shadow"></span>
      <span class="edge"></span>
      <span class="front">重新開始</span>
    `;
        btn.setAttribute('onclick', 'resetQuiz()');
    }

    function resetQuiz() {
        resetProgress();
        correctCount = 0;
        wrongCount = 0;
        usedIndices = [];
        currentQuestion = 0;
        document.getElementById('correct-count').textContent = 0;
        document.getElementById('wrong-count').textContent = 0;
        document.getElementById('current-question').textContent = 0;
        document.getElementById('accuracy').textContent = "0%";
        document.getElementById('progress').textContent = "0%";
        document.getElementById('result').textContent = '';
        document.getElementById('result2').textContent = '';
        document.getElementById('user-input').value = '';
        document.getElementById('completion-progress').style.width = '0%';
        document.getElementById('accuracy-progress').style.width = '0%';
        currentIndex = getRandomIndex();
        currentQuestion++;
        loadQuestion();
        const btn = document.getElementById('check-button');
        btn.innerHTML = originalCheckButtonHTML;
        btn.setAttribute('onclick', 'checkAnswer()');
    }

    function updateProgressChart() {
        const total = jsonData.length;
        const completed = usedIndices.length;
        const completion = (completed / total) * 100;
        const attempts_cnt = correctCount + wrongCount
        const accuracy = attempts_cnt != 0 ? (correctCount / attempts_cnt) * 100 : 0;

        if (accuracy > 100) {
            accuracy = 100;
        }

        document.getElementById('completion-progress').style.width = `${completion}%`;
        document.getElementById('completion-text').textContent = `${correctCount} / ${total} (${Math.round(completion)}%)`;
        document.getElementById('accuracy-progress').style.width = `${accuracy}%`;
        document.getElementById('accuracy-text').textContent = `${Math.round(accuracy)}%`;
    }
    window.resetQuiz = resetQuiz;


    function toggleMode() {
        const button = document.getElementById('toggle-button');
        mode = (mode + 1) % 3;
        button.textContent = modestr[mode];
        loadQuestion();
    }

    function checkOnEnter(event) {
        if (event.key === 'Enter') {
            const nextBtn = document.getElementById('next-button');
            nextBtn.style.display === 'flex' ? nextQuestion() : checkAnswer();
        }
    }

    function setCookie(name, value, days) {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${d.toUTCString()};path=/`;
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let c of ca) {
            c = c.trim();
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length);
        }
        return null;
    }

    function storeProgress() {
        setCookie('correctCount', correctCount, 7);
        setCookie('wrongCount', wrongCount, 7);
        setCookie('usedIndices', JSON.stringify(usedIndices), 7);
    }

    function resetProgress() {
        setCookie('correctCount', '', -1);
        setCookie('wrongCount', '', -1);
        setCookie('usedIndices', '', -1);
        correctCount = 0;
        wrongCount = 0;
        usedIndices = [];
        currentQuestion = 0;
        currentIndex = getRandomIndex();
        loadQuestion();
        updateProgressChart();
    }

    function loadProgress() {
        const savedScale = getCookie('pageScale');
        if (savedScale) {
            const scaleValue = parseFloat(savedScale);
            questionContainer.style.transform = `scale(${scaleValue})`;
            slider.value = scaleValue * 400;
        }

        const storedCorrectCount = getCookie('correctCount');
        const storedWrongCount = getCookie('wrongCount');
        const storedUsedIndices = getCookie('usedIndices');

        if (storedCorrectCount !== null) {
            correctCount = parseInt(storedCorrectCount, 10);
            document.getElementById('correct-count').textContent = correctCount;
        }
        if (storedWrongCount !== null) {
            wrongCount = parseInt(storedWrongCount, 10);
            document.getElementById('wrong-count').textContent = wrongCount;
        }
        if (storedUsedIndices !== null) {
            usedIndices = JSON.parse(storedUsedIndices);
        }
        currentQuestion = correctCount + wrongCount;
        document.getElementById('current-question').textContent = currentQuestion;
        currentIndex = getRandomIndex();
        loadQuestion();
        if (usedIndices.length === jsonData.length) {
            document.getElementById('result2').textContent = '已完成作答！';
            const nextButton = document.getElementById('next-button');
            nextButton.style.display = 'none';
            const checkElement = document.getElementById('check-button');
            checkElement.style.display = 'flex';
            changeCheckButtonToReset();
        }
    }

    // 事件綁定
    $('#reset-button').click(resetQuiz);
    $('#check-button').click(checkAnswer);
    $('#next-button').click(nextQuestion);
    $('#user-input').keypress(checkOnEnter);
    $('#toggle-button').click(toggleMode);

    slider.addEventListener('input', function () {
        const scaleValue = slider.value / 400;
        questionContainer.style.transform = `scale(${scaleValue})`;
        setCookie('pageScale', scaleValue, 7);
    });

    
    jsonData = words;
    document.getElementById('qcount').textContent = words.length;
    originalCheckButtonHTML = checkButtonElem.innerHTML; // 這裡不會報錯

    loadProgress();
});
