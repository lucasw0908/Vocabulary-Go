import $ from 'jquery';

$(function () {
  let jsonData = words; // 從後端傳來的字卡資料 [{English, Chinese}]
  let currentIndex = 0;
  let total = jsonData.length;

  let hasFlipped = false;
  let showFlipHint = true; 

  const cardElem = $('#flashcard');
  const wordFront = $('#word-front');
  const wordBack = $('#word-back');
  const prevBtn = $('#prev-button');
  const nextBtn = $('#next-button');

  $('#total-card').text(total);
  loadCard(currentIndex);
  updateProgress();

  function loadCard(index) {
    const word = jsonData[index];
    wordFront.text(word.English);
    wordBack.text(word.Chinese);
    $('#current-card').text(index + 1);



    if (showFlipHint) {
      $('#flip-hint').show();
    } else {
      $('#flip-hint').hide();
    }

    if (index === 0) {
      prevBtn.prop('disabled', true).addClass('disabled');
    } else {
      prevBtn.prop('disabled', false).removeClass('disabled');
    }

    if (index === total - 1) {
      nextBtn.prop('disabled', true).addClass('disabled');
    } else {
      nextBtn.prop('disabled', false).removeClass('disabled');
    }
  }

  function updateProgress() {
    const completion = ((currentIndex + 1) / total) * 100;
    $('#completion-progress').css('width', `${completion}%`);
  }

  cardElem.on('click', function () {
    $(this).toggleClass('flip');
    hasFlipped = $(this).hasClass('flip'); 
    showFlipHint = false;
    $('#flip-hint').fadeOut();
  });
  
  prevBtn.click(prevCard);
  nextBtn.click(nextCard);

  function nextCard() {
    if (currentIndex < total - 1) {
      currentIndex++;
      loadCard(currentIndex);
      updateProgress();
    }
  }

  function prevCard() {
    if (currentIndex > 0) {
      currentIndex--;
      loadCard(currentIndex);
      updateProgress();
    }
  }

  $('#reset-button').click(function () {
    currentIndex = 0;
    loadCard(currentIndex);
    updateProgress();
    showFlipHint = true;
  });
});
