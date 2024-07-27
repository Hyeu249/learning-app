/** @odoo-module */

import {
    Component,
    useState,
    onMounted,
    useRef,
    xml,
    useEffect,
} from "@odoo/owl"

export class Header extends Component {
    static template = "Header"
    static components = {}

    setup() {}
}

export class Body extends Component {
    static template = "Body"
    static components = { Button }
    currentSlide = 0
    slideInterval = 3000
    slideTimer

    setup() {
        useEffect(
            () => {
                this.appendStyle()

                this.showSlide(this.currentSlide)
                this.slideTimer = setInterval(() => {
                    this.moveSlide(1)
                }, this.slideInterval)

                return () => clearInterval(this.slideTimer)
            },
            () => []
        )
    }

    showSlide(index) {
        const slides = document.querySelectorAll(".carousel-images div")
        if (index >= slides.length) {
            this.currentSlide = 0
        } else if (index < 0) {
            this.currentSlide = slides.length - 1
        } else {
            this.currentSlide = index
        }
        const offset = -this.currentSlide * 100
        document.querySelector(
            ".carousel-images"
        ).style.transform = `translateX(${offset}%)`
    }

    moveSlide(step, slideIndex) {
        if (slideIndex) {
            this.showSlide(slideIndex)
        } else {
            this.showSlide(this.currentSlide + step)
        }
        this.resetSlideTimer()
    }

    resetSlideTimer() {
        clearInterval(this.slideTimer)
        this.slideTimer = setInterval(() => {
            this.moveSlide(1)
        }, this.slideInterval)
    }

    handleCategoryClick(event) {
        // Remove background color from all categories
        document.querySelectorAll(".score-category div").forEach((div) => {
            div.style.backgroundColor = ""
        })

        // Set background color for the clicked category
        event.currentTarget.style.backgroundColor = "#dfe6e9" // Change color as desired
    }

    changeBackgroundColorAndMoveSlide(event, slideIndex) {
        this.handleCategoryClick(event)
        this.moveSlide(false, slideIndex)
    }

    openDashboard() {
        alert("Dashboard button clicked!")
    }

    openSettings() {
        alert("Settings button clicked!")
    }

    openProfile() {
        alert("Profile button clicked!")
    }

    appendStyle() {
        var style = document.createElement("style")
        var css = this.getCss()

        style.appendChild(document.createTextNode(css))
        const whatsup = document.getElementById("lang_app_body")

        whatsup.appendChild(style)
    }

    getCss() {
        return `
        .sidebar {
            width: 250px;
            background-color: #4CAF50;
            color: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
        }

        .content {
            flex: 1;
            align-items: center;
            padding: 20px;
            background-color: white;
        }

        .sidebar-button {
            background-color: #ffffff;
            color: #4CAF50;
            border: none;
            padding: 10px 20px;
            margin: 10px;
            cursor: pointer;
            border-radius: 5px;
            font-size: 16px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            transition: background-color 0.3s, box-shadow 0.3s;
        }

        .sidebar-button:hover {
            background-color: #e8e8e8;
        }

        .sidebar-button:active {
            background-color: #d0d0d0;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }

        .carousel {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 600px;
            background-color: white;
            box-shadow: rgba(0, 0, 0, 0.25) 0px 0.125rem 0.25rem 0px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            z-index: 1000;
        }

        .carousel-images {
            display: flex;
            transition: transform 0.5s ease;
            width: calc(3 * 100%);
        }

        .carousel-images div {
            width: 100%;
            height: 120px;
            flex: 0 0 auto;
        }

        .carousel button {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            padding: 10px;
            cursor: pointer;
            z-index: 1;
        }

        .prev {
            left: 10px;
        }

        .next {
            right: 10px;
        }

        /* Additional styles for the content area */
        .container {
            background-color: white;
            border-radius: 8px;
            box-shadow: rgba(0, 0, 0, 0.25) 0px 0.125rem 0.25rem 0px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header .level {
            background-color: #ffcc00;
            color: #000;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }

        .progress-bar {
            margin: 20px 0;
            height: 10px;
            background-color: #f1f1f1;
            border-radius: 5px;
            overflow: hidden;
        }

        .progress-bar-inner {
            width: 50%;
            background-color: #4CAF50;
            height: 100%;
        }

        .score-section {
            background-color: #ffeb99;
            padding: 10px;
            border-radius: 5px;
        }

        .score-section .title {
            font-weight: bold;
            margin-bottom: 10px;
        }

        .score-section .score {
            font-size: 24px;
            font-weight: bold;
            text-align: right;
        }

        .score-category {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            cursor: pointer; /* Add cursor to indicate clickable items */
        }

        .score-category div {
            text-align: center;
            flex: 1;
            padding: 10px;
            transition: background-color 0.3s; /* Smooth transition */
        }

        .score-category div:not(:last-child) {
            border-right: 1px solid #ccc;
        }

        .score-category .category-title {
            font-weight: bold;
        }

        .score-category .category-score {
            font-size: 24px;
            font-weight: bold;
        }
    `
    }
}
