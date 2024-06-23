 document.addEventListener('DOMContentLoaded', function() {
                var urlParams = new URLSearchParams(window.location.search);
                var section = urlParams.get('section');
                var message = urlParams.get('message');
                if (section) {
                    showSection(section);
                }
                if (message && section === 'settings') {
                    var messageDiv = document.createElement('div');
                    messageDiv.className = 'alert alert-success';
                    messageDiv.textContent = message;
                    document.getElementById(section).prepend(messageDiv);
                }
            });

            window.addEventListener('DOMContentLoaded', (event) => {
                if (window.location.search.indexOf('message=') >= 0) {
                    let clean_uri = window.location.protocol + "//" + window.location.host + window.location.pathname;
                    window.history.replaceState({}, document.title, clean_uri);
                }
            });

            function showSection(sectionId) {
                document.querySelectorAll('.menu span, .menu img').forEach(element => {
                    element.classList.remove('active');
                });

                document.querySelectorAll('div[id]').forEach(div => {
                    div.style.display = 'none';
                });

                document.getElementById(sectionId).style.display = 'block';
                document.querySelector(`.menu span[onclick="showSection('${sectionId}')"]`)?.classList.add('active');
                document.querySelector(`.menu img[onclick="showSection('${sectionId}')"]`)?.classList.add('active');
            }