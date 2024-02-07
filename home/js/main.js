var button;
var dots = 0;
var dotsInterval;

function askQuestion() {
    var text = document.getElementById('question').value;
    button = document.querySelector('button');
    button.disabled = true;
    button.innerText = '質問中';
    button.classList.add('loading');

    // Start the dots animation
    dotsInterval = setInterval(function () {
        dots = (dots + 1) % 4;
        button.innerText = '質問中' + '.'.repeat(dots);
    }, 500);

    // Clear the previous answer and images
    document.getElementById('answer').innerText = '';
    document.getElementById('error').innerText = '';

    if (text.startsWith('!image ')) {
        var imagePrompt = text.slice(7);
        fetch('/generate_image?prompt=' + encodeURIComponent(imagePrompt))
            .then(response => response.json())
            .then(data => {
                data.images.forEach(imageData => {
                    var img = document.createElement('img');
                    img.src = 'data:image/png;base64,' + imageData;
                    img.style.width = '300px';  // 画像の幅を300pxに制限
                    document.getElementById('answer').appendChild(img);
                });
                clearInterval(dotsInterval);
                button.innerText = '質問する';
                button.classList.remove('loading');
                setTimeout(function () {
                    button.disabled = false;
                }, 3000);
            })
            .catch(error => {
                console.error('Error:', error);
                clearInterval(dotsInterval);
                document.getElementById('error').innerText = 'エラーが起きました';
                button.innerText = '質問する';
                button.classList.remove('loading');
                button.disabled = false;
            });
    } else {
        fetch('/ask?text=' + encodeURIComponent(text))
            .then(response => response.json())
            .then(data => {
                var decodedData = unicodeToUtf8(data);
                document.getElementById('answer').innerText = decodedData;
                clearInterval(dotsInterval);
                button.innerText = '質問する';
                button.classList.remove('loading');
                setTimeout(function () {
                    button.disabled = false;
                }, 3000);
            })
            .catch(error => {
                console.error('Error:', error);
                clearInterval(dotsInterval);
                document.getElementById('error').innerText = 'エラーが起きました';
                button.innerText = '質問する';
                button.classList.remove('loading');
                button.disabled = false;
            });


    }
}


function unicodeToUtf8(unicode) {
    return unicode.replace(/\\u([a-fA-F0-9]{4})/g, function (match, grp) {
        return String.fromCharCode(parseInt(grp, 16));
    });
}

window.onload = function () {
    var textarea = document.getElementById('question');
    textarea.addEventListener('input', autoResize, false);
    textarea.addEventListener('keyup', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            askQuestion();
        }
        autoResize.call(this);
    }, false);
    textarea.addEventListener('focus', function () {
        this.classList.add('focused');
    }, false);
    textarea.addEventListener('blur', function () {
        this.classList.remove('focused');
    }, false);

    function autoResize() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    }

    // Call autoResize at the beginning to adjust the initial text.
    autoResize.call(textarea);

    button = document.querySelector('button');
    button.addEventListener('mouseover', function () {
        this.classList.add('hovered');
    }, false);
    button.addEventListener('mouseout', function () {
        this.classList.remove('hovered');
    }, false);

}