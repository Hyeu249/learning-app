class BodyHome extends Component {
    
    setup(){
        this.currentSlide = 0;
        this.slideInterval = 3000;
        this.slideTimer;

        onMounted(this.onMounted)
    }

    onMounted(){
        this.showSlide(this.currentSlide)
        this.slideTimer = setInterval(() => {
            this.moveSlide(1);
        }, this.slideInterval);
    }

    showSlide(index) {
        const slides = document.querySelectorAll('.carousel-images div');
        if (index >= slides.length) {
            this.currentSlide = 0;
        } else if (index < 0) {
            this.currentSlide = slides.length - 1;
        } else {
            this.currentSlide = index;
        }
        const offset = -this.currentSlide * 100;
        document.querySelector('.carousel-images').style.transform = `translateX(${offset}%)`;
    }

    moveSlide(step, slideIndex) {
        console.log(step, slideIndex)
        if (slideIndex){
            this.showSlide(slideIndex);
        }else{
            this.showSlide(this.currentSlide + step);
        }
        this.resetSlideTimer();
    }

    resetSlideTimer() {
        clearInterval(this.slideTimer);
        this.slideTimer = setInterval(() => {
            this.moveSlide(1);
        }, this.slideInterval);
    }

    handleCategoryClick(event) {
        // Remove background color from all categories
        document.querySelectorAll('.score-category div').forEach(div => {
            div.style.backgroundColor = '';
        });

        // Set background color for the clicked category
        event.currentTarget.style.backgroundColor = '#dfe6e9'; // Change color as desired
    }

    changeBackgroundColorAndMoveSlide(event, slideIndex){
        handleCategoryClick(event)
        moveSlide(false, slideIndex)
    }

    openDashboard() {
        alert('Dashboard button clicked!');
    }

    openSettings() {
        alert('Settings button clicked!');
    }

    openProfile() {
        alert('Profile button clicked!');
    }

}