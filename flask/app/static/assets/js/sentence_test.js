import $ from 'jquery';

$(function () {
    let jsonData = new Set();

    let currentQuestion = 0;
    let correctCount = 0;
    let wrongCount = 0;
    let usedIndices = new Set();
    let currentIndex;
    const checkButtonElem = document.getElementById('check-button');
    let originalCheckButtonHTML = checkButtonElem.innerHTML;
    const slider = document.getElementById('resize-slider');
    const questionContainer = document.getElementById('question-container');
    const nextButton = document.getElementById('next-button');

    let currentQuestionData = {
        chinese: '',
        english: '',
        word_chinese: '',
        word_english: ''
    };

    jsonData = new Set(questions.filter(item => item.english && item.english.trim() !== ''));
    document.getElementById('qcount').textContent = jsonData.size;
    loadProgress();

    function updateProgressChart() {
        const total = jsonData.size;
        const completed = usedIndices.size;
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


    // Function to set a cookie
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + date.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/";
    }

    // Function to get a cookie
    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i].trim();
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    function storeProgress() {
        setCookie('s-correctCount', correctCount, 7);
        setCookie('s-wrongCount', wrongCount, 7);
        setCookie('s-usedIndices', JSON.stringify(Array.from(usedIndices)), 7);
    }

    function loadProgress() {
        updateProgressChart();
        const savedScale = getCookie('pageScale');
        if (savedScale) {
            const scaleValue = parseFloat(savedScale);
            questionContainer.style.transform = `scale(${scaleValue})`;
            slider.value = scaleValue * 400;
        }

        const storedCorrectCount = getCookie('s-correctCount');
        const storedWrongCount = getCookie('s-wrongCount');
        const storedUsedIndices = getCookie('s-usedIndices');

        if (storedCorrectCount !== null) {
            correctCount = parseInt(storedCorrectCount, 10);
            document.getElementById('correct-count').textContent = correctCount;
        }
        if (storedWrongCount !== null) {
            wrongCount = parseInt(storedWrongCount, 10);
            document.getElementById('wrong-count').textContent = wrongCount;
        }
        if (storedUsedIndices !== null) {
            usedIndices = new Set(JSON.parse(storedUsedIndices));
        }
        currentQuestion = correctCount + wrongCount;
        document.getElementById('current-question').textContent = currentQuestion;
        currentIndex = getRandomIndex();

        if (usedIndices.size === jsonData.size) {
            document.getElementById('result2').textContent = '已完成作答！';
            nextButton.style.display = 'none';
            const checkElement = document.getElementById('check-button');
            checkElement.style.display = 'flex';
            changeCheckButtonToReset();
        }

        loadQuestion();
    }

    function getRandomIndex() {
        const dataArray = Array.from(jsonData);
        const validIndices = dataArray
            .map((item, index) => ({ index, item }))
            .filter(({ index }) => !usedIndices.has(index));

        if (validIndices.length === 0) return null;

        const randomItem = validIndices[Math.floor(Math.random() * validIndices.length)];
        return randomItem.index;
    }


    function loadQuestion() {
        if (currentIndex === null) return;
        const arrayData = Array.from(jsonData);
        currentQuestionData = arrayData[currentIndex];
        console.log(currentQuestionData)
        if (currentQuestionData.english === "" || currentQuestionData.english == null) {
            console.log("haha it's empty!")
            nextQuestion();
        }


        document.getElementById('current-question').textContent = currentQuestion;
        const chineseWordElement = document.getElementById('chinese-word');
        const englishWordElement = document.getElementById('english-word');
        chineseWordElement.textContent = currentQuestionData.chinese;
        englishWordElement.textContent = currentQuestionData.english;
        updateProgressChart();
        console.log("rendered!")
    }


    // Update the function to save zprogress after checking each answer
    function checkAnswer() {
        if (usedIndices.length >= jsonData.size) return;
        const checkElement = document.getElementById('check-button');
        checkElement.style.display = 'none';
        const userInput = document.getElementById('user-input').value.toLowerCase();
        const correctAnswer = currentQuestionData.word_english.toLowerCase();
        const resultElement = document.getElementById('result');
        const resultsElement = document.getElementById('result2');

        if (userInput.trim() == correctAnswer.trim()) {
            resultElement.textContent = '正確！';
            nextButton.style.display = ''; // 顯示下一題按鈕
            usedIndices.add(currentIndex);
            correctCount++;
            document.getElementById('correct-count').textContent = correctCount;
        } else {
            resultElement.textContent = '錯誤，正確答案是 : ' + correctAnswer;
            nextButton.style.display = ''; // 顯示下一題按鈕
            wrongCount++;
            document.getElementById('wrong-count').textContent = wrongCount;
        }

        currentQuestion++;
        nextButton.style.display = 'flex';
        checkButtonElem.style.display = 'none';
        document.getElementById('correct-count').textContent = correctCount;
        document.getElementById('wrong-count').textContent = wrongCount;
        updateProgressChart();
        storeProgress();
        if (usedIndices.length === jsonData.size) {
            document.getElementById('result2').textContent = '已完成作答！';
            nextButton.style.display = 'none';
            const checkElement = document.getElementById('check-button');
            checkElement.style.display = 'flex';
            changeCheckButtonToReset();
        }

    }
    window.checkAnswer = checkAnswer;


    function nextQuestion() {

        if (usedIndices.length === jsonData.size) return;
        storeProgress();
        document.getElementById('next-button').style.display = 'none';

        checkButtonElem.style.display = 'flex';
        document.getElementById('user-input').value = '';
        document.getElementById('result').textContent = '';
        document.getElementById('result2').textContent = '';
        currentIndex = getRandomIndex();
        if (currentIndex !== null) loadQuestion();
    }


    function resetQuiz() {
        resetProgress();
        correctCount = 0;
        wrongCount = 0;
        usedIndices.clear();
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
    window.resetQuiz = resetQuiz;

    function changeCheckButtonToReset() {
        const btn = document.getElementById('check-button');
        btn.innerHTML = `
      <span class="shadow"></span>
      <span class="edge"></span>
      <span class="front">重新開始</span>
    `;
        btn.setAttribute('onclick', 'resetQuiz()');
    }




    function checkOnEnter(event) {
        if (event.key === 'Enter') {
            nextButton.style.display === 'flex' ? nextQuestion() : checkAnswer();
        }
    }



    function resetProgress() {
        setCookie('s-correctCount', '', -1);
        setCookie('s-wrongCount', '', -1);
        setCookie('s-usedIndices', '', -1);
        correctCount = 0;
        wrongCount = 0;
        usedIndices.clear();
        currentQuestion = 0;
        currentIndex = getRandomIndex();
        loadQuestion();
        updateProgressChart();
    }



    // 事件綁定
    $('#reset-button').click(resetQuiz);
    $('#check-button').click(checkAnswer);
    $('#next-button').click(nextQuestion);
    $('#user-input').keypress(checkOnEnter);

    slider.addEventListener('input', function () {
        const scaleValue = slider.value / 400;
        questionContainer.style.transform = `scale(${scaleValue})`;
        setCookie('pageScale', scaleValue, 7);
    });

    // 初始化

});
