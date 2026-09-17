document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // InterviewIQ - Frontend Application
    // ==========================================

    const welcomeSection = document.getElementById("welcome");
    const interviewSection = document.getElementById("interview");
    const reportSection = document.getElementById("report");
    const historySection = document.getElementById("history");

    const roleSelect = document.getElementById("roleSelect");
    const startButton = document.getElementById("startButton");

    const roleName = document.getElementById("roleName");
    const progressText = document.getElementById("progressText");
    const progressBar = document.getElementById("progressBar");

    const questionElement = document.getElementById("question");
    const answerBox = document.getElementById("answer");
    const wordCount = document.getElementById("wordCount");

    const submitButton = document.getElementById("submitButton");
    const nextButton = document.getElementById("nextButton");
    const feedbackBox = document.getElementById("feedback");

    const restartButton = document.getElementById("restartButton");

    const overallScore = document.getElementById("overallScore");
    const performanceLevel = document.getElementById("performanceLevel");
    const reportSummary = document.getElementById("reportSummary");
    const answerReview = document.getElementById("answerReview");

    const historyButton = document.getElementById("historyButton");
    const closeHistory = document.getElementById("closeHistory");
    const historyList = document.getElementById("historyList");


    // ==========================================
    // Interview State
    // ==========================================

    let interviewId = null;
    let selectedRole = "";
    let questions = [];
    let currentQuestionIndex = 0;


    // ==========================================
    // Show Section
    // ==========================================

    function showSection(section) {
        [
            welcomeSection,
            interviewSection,
            reportSection,
            historySection
        ].forEach((element) => {
            if (element) {
                element.classList.add("hidden");
            }
        });

        if (section) {
            section.classList.remove("hidden");
        }

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }


    // ==========================================
    // Normalize Category
    // ==========================================

    function normalizeLabel(label) {
        if (!label) {
            return "Weak";
        }

        const value = String(label)
            .trim()
            .toLowerCase();

        if (value === "strong") {
            return "Strong";
        }

        if (value === "average") {
            return "Average";
        }

        if (value === "weak") {
            return "Weak";
        }

        return "Weak";
    }


    // ==========================================
    // Word Counter
    // ==========================================

    function updateWordCount() {
        if (!answerBox || !wordCount) {
            return;
        }

        const text = answerBox.value.trim();

        if (!text) {
            wordCount.textContent = "0 words";
            return;
        }

        const words = text
            .split(/\s+/)
            .filter(Boolean);

        wordCount.textContent =
            `${words.length} ${
                words.length === 1 ? "word" : "words"
            }`;
    }


    // ==========================================
    // Button Loading
    // ==========================================

    function setButtonLoading(button, text) {
        if (!button) {
            return;
        }

        button.disabled = true;

        button.dataset.originalHTML =
            button.innerHTML;

        button.innerHTML = text;
    }


    function restoreButton(button) {
        if (!button) {
            return;
        }

        button.disabled = false;

        if (button.dataset.originalHTML) {
            button.innerHTML =
                button.dataset.originalHTML;

            delete button.dataset.originalHTML;
        }
    }


    // ==========================================
    // Error Message
    // ==========================================

    function showError(message) {
        alert(message);
    }


    // ==========================================
    // Load Roles
    // ==========================================

    async function loadRoles() {
        try {
            const response =
                await fetch("/api/roles");

            if (!response.ok) {
                throw new Error(
                    `Failed to load roles (${response.status})`
                );
            }

            const data =
                await response.json();

            roleSelect.innerHTML = "";

            if (
                !data.roles ||
                data.roles.length === 0
            ) {
                const option =
                    document.createElement("option");

                option.textContent =
                    "No roles available";

                option.disabled = true;
                option.selected = true;

                roleSelect.appendChild(option);

                startButton.disabled = true;

                return;
            }

            data.roles.forEach((role) => {
                const option =
                    document.createElement("option");

                option.value = role;
                option.textContent = role;

                roleSelect.appendChild(option);
            });

            startButton.disabled = false;

        } catch (error) {
            console.error(
                "Role loading error:",
                error
            );

            roleSelect.innerHTML = "";

            const option =
                document.createElement("option");

            option.textContent =
                "Unable to load roles";

            option.disabled = true;
            option.selected = true;

            roleSelect.appendChild(option);

            startButton.disabled = true;

            showError(
                "Could not load job roles. " +
                "Please make sure the FastAPI server is running."
            );
        }
    }


    // ==========================================
    // Start Interview
    // ==========================================

    async function startInterview() {
        const role = roleSelect.value;

        if (!role) {
            showError(
                "Please select a job role first."
            );

            return;
        }

        try {
            setButtonLoading(
                startButton,
                "Starting..."
            );

            const response =
                await fetch(
                    "/api/interviews",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            role: role
                        })
                    }
                );

            if (!response.ok) {
                let message =
                    "Unable to start interview.";

                try {
                    const errorData =
                        await response.json();

                    if (errorData.detail) {
                        message =
                            errorData.detail;
                    }
                } catch (_) {}

                throw new Error(message);
            }

            const data =
                await response.json();

            interviewId =
                data.interview_id;

            selectedRole =
                data.role;

            questions =
                data.questions || [];

            currentQuestionIndex = 0;

            if (questions.length === 0) {
                throw new Error(
                    "No interview questions were returned."
                );
            }

            roleName.textContent =
                selectedRole;

            showQuestion();

            showSection(
                interviewSection
            );

        } catch (error) {
            console.error(
                "Start interview error:",
                error
            );

            showError(
                error.message ||
                "Unable to start the interview."
            );

        } finally {
            restoreButton(startButton);
        }
    }


    // ==========================================
    // Show Question
    // ==========================================

    function showQuestion() {
        const currentQuestion =
            questions[currentQuestionIndex];

        if (!currentQuestion) {
            return;
        }

        questionElement.textContent =
            currentQuestion.question;

        progressText.textContent =
            `Question ${
                currentQuestionIndex + 1
            } of ${questions.length}`;

        const progress =
            (
                (currentQuestionIndex + 1) /
                questions.length
            ) * 100;

        progressBar.style.width =
            `${progress}%`;

        answerBox.value = "";

        updateWordCount();

        feedbackBox.innerHTML = "";

        feedbackBox.classList.add(
            "hidden"
        );

        nextButton.classList.add(
            "hidden"
        );

        submitButton.classList.remove(
            "hidden"
        );

        submitButton.disabled = false;

        submitButton.innerHTML =
            'Analyse answer <span>→</span>';

        answerBox.disabled = false;

        answerBox.focus();
    }


    // ==========================================
    // Submit Answer
    // ==========================================

    async function submitAnswer() {
        const answer =
            answerBox.value.trim();

        if (!answer) {
            showError(
                "Please write your answer first."
            );

            answerBox.focus();

            return;
        }

        if (!interviewId) {
            showError(
                "Interview session is not available."
            );

            return;
        }

        try {
            setButtonLoading(
                submitButton,
                "Analysing..."
            );

            const response =
                await fetch(
                    "/api/answers",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            interview_id:
                                interviewId,

                            question_index:
                                currentQuestionIndex,

                            answer:
                                answer
                        })
                    }
                );

            if (!response.ok) {
                let message =
                    "Unable to evaluate the answer.";

                try {
                    const errorData =
                        await response.json();

                    if (errorData.detail) {
                        message =
                            errorData.detail;
                    }
                } catch (_) {}

                throw new Error(message);
            }

            const result =
                await response.json();

            console.log(
                "InterviewIQ evaluation:",
                result
            );

            // ==================================
            // IMPORTANT
            // Only category + feedback is shown.
            //
            // NO:
            // score
            // percentage
            // similarity
            // confidence
            // method
            // ==================================

            const label =
                normalizeLabel(
                    result.label
                );

            showFeedback(
                label,
                result.feedback || ""
            );

            answerBox.disabled = true;

            submitButton.classList.add(
                "hidden"
            );

            nextButton.classList.remove(
                "hidden"
            );

            if (
                currentQuestionIndex <
                questions.length - 1
            ) {
                nextButton.innerHTML =
                    'Continue to next question <span>→</span>';
            } else {
                nextButton.innerHTML =
                    'View final report <span>→</span>';
            }

        } catch (error) {
            console.error(
                "Answer evaluation error:",
                error
            );

            showError(
                error.message ||
                "The answer could not be evaluated."
            );

            restoreButton(
                submitButton
            );
        }
    }


    // ==========================================
    // Show Feedback
    // ==========================================

    function showFeedback(
        label,
        feedback
    ) {
        feedbackBox.innerHTML = "";

        const category =
            document.createElement("strong");

        category.textContent =
            label;

        category.className =
            `evaluation-category ${
                label.toLowerCase()
            }`;

        feedbackBox.appendChild(
            category
        );

        if (feedback) {
            const feedbackText =
                document.createElement("p");

            feedbackText.textContent =
                feedback;

            feedbackBox.appendChild(
                feedbackText
            );
        }

        feedbackBox.classList.remove(
            "hidden"
        );
    }


    // ==========================================
    // Next Question
    // ==========================================

    async function nextQuestion() {
        if (
            currentQuestionIndex <
            questions.length - 1
        ) {
            currentQuestionIndex++;

            showQuestion();

        } else {
            await finishInterview();
        }
    }


    // ==========================================
    // Finish Interview
    // ==========================================

    async function finishInterview() {
        if (!interviewId) {
            return;
        }

        try {
            setButtonLoading(
                nextButton,
                "Preparing report..."
            );

            const response =
                await fetch(
                    `/api/interviews/${interviewId}/finish`,
                    {
                        method: "POST"
                    }
                );

            if (!response.ok) {
                let message =
                    "Unable to generate final report.";

                try {
                    const errorData =
                        await response.json();

                    if (errorData.detail) {
                        message =
                            errorData.detail;
                    }
                } catch (_) {}

                throw new Error(message);
            }

            const report =
                await response.json();

            showReport(report);

        } catch (error) {
            console.error(
                "Finish interview error:",
                error
            );

            showError(
                error.message ||
                "Could not generate the final report."
            );

            restoreButton(
                nextButton
            );
        }
    }


    // ==========================================
    // Final Report
    // ==========================================

    function showReport(report) {
        const label =
            normalizeLabel(
                report.label
            );

        // Existing HTML IDs are reused,
        // but NO numeric score is displayed.

        if (overallScore) {
            overallScore.textContent =
                label;

            overallScore.className =
                `category-result ${
                    label.toLowerCase()
                }`;
        }

        if (performanceLevel) {
            performanceLevel.textContent =
                label;

            performanceLevel.className =
                `performance-category ${
                    label.toLowerCase()
                }`;
        }

        if (reportSummary) {
            reportSummary.textContent =
                `Your interview session has been evaluated as ${label}.`;
        }

        renderAnswerReview(
            report.answers || []
        );

        showSection(
            reportSection
        );
    }


    // ==========================================
    // Answer Review
    // ==========================================

    function renderAnswerReview(
        answers
    ) {
        answerReview.innerHTML = "";

        if (
            !answers ||
            answers.length === 0
        ) {
            answerReview.innerHTML =
                "<p>No answer review is available.</p>";

            return;
        }

        answers.forEach(
            (item, index) => {
                const label =
                    normalizeLabel(
                        item.label
                    );

                const review =
                    document.createElement("div");

                review.className =
                    "review";

                const badge =
                    document.createElement("div");

                badge.className =
                    `badge ${
                        label.toLowerCase()
                    }`;

                badge.textContent =
                    `QUESTION ${index + 1} · ${label.toUpperCase()}`;

                const question =
                    document.createElement("h3");

                question.textContent =
                    item.question || "";

                const feedback =
                    document.createElement("p");

                feedback.textContent =
                    item.feedback || "";

                review.appendChild(
                    badge
                );

                review.appendChild(
                    question
                );

                review.appendChild(
                    feedback
                );

                answerReview.appendChild(
                    review
                );
            }
        );
    }


    // ==========================================
    // History
    // ==========================================

    async function loadHistory() {
        try {
            historyList.innerHTML =
                "<p>Loading history...</p>";

            const response =
                await fetch(
                    "/api/history"
                );

            if (!response.ok) {
                throw new Error(
                    `Failed to load history (${response.status})`
                );
            }

            const data =
                await response.json();

            renderHistory(
                data.history || []
            );

            showSection(
                historySection
            );

        } catch (error) {
            console.error(
                "History loading error:",
                error
            );

            historyList.innerHTML =
                "<p>Unable to load practice history.</p>";

            showSection(
                historySection
            );
        }
    }


    // ==========================================
    // Render History
    // ==========================================

    function renderHistory(
        history
    ) {
        historyList.innerHTML = "";

        if (
            !history ||
            history.length === 0
        ) {
            historyList.innerHTML =
                "<p>No practice sessions yet.</p>";

            return;
        }

        history.forEach(
            (item) => {
                const label =
                    normalizeLabel(
                        item.label
                    );

                const historyItem =
                    document.createElement("div");

                historyItem.className =
                    "history-item";

                const role =
                    document.createElement("strong");

                role.textContent =
                    item.role || "Interview";

                const date =
                    document.createElement("small");

                date.textContent =
                    formatDate(
                        item.started_at
                    );

                const category =
                    document.createElement("span");

                category.textContent =
                    label;

                category.className =
                    `history-score ${
                        label.toLowerCase()
                    }`;

                historyItem.appendChild(
                    role
                );

                historyItem.appendChild(
                    date
                );

                historyItem.appendChild(
                    category
                );

                historyList.appendChild(
                    historyItem
                );
            }
        );
    }


    // ==========================================
    // Date Formatter
    // ==========================================

    function formatDate(value) {
        if (!value) {
            return "";
        }

        try {
            const date =
                new Date(value);

            if (
                Number.isNaN(
                    date.getTime()
                )
            ) {
                return String(value);
            }

            return date.toLocaleString();

        } catch (_) {
            return String(value);
        }
    }


    // ==========================================
    // Restart Interview
    // ==========================================

    function restartInterview() {
        interviewId = null;
        selectedRole = "";
        questions = [];
        currentQuestionIndex = 0;

        answerBox.value = "";

        updateWordCount();

        showSection(
            welcomeSection
        );
    }


    // ==========================================
    // Event Listeners
    // ==========================================

    if (startButton) {
        startButton.addEventListener(
            "click",
            startInterview
        );
    }

    if (submitButton) {
        submitButton.addEventListener(
            "click",
            submitAnswer
        );
    }

    if (nextButton) {
        nextButton.addEventListener(
            "click",
            nextQuestion
        );
    }

    if (restartButton) {
        restartButton.addEventListener(
            "click",
            restartInterview
        );
    }

    if (answerBox) {
        answerBox.addEventListener(
            "input",
            updateWordCount
        );
    }

    if (historyButton) {
        historyButton.addEventListener(
            "click",
            loadHistory
        );
    }

    if (closeHistory) {
        closeHistory.addEventListener(
            "click",
            () => {
                showSection(
                    welcomeSection
                );
            }
        );
    }


    // ==========================================
    // Initial Application Load
    // ==========================================

    loadRoles();
    updateWordCount();
});