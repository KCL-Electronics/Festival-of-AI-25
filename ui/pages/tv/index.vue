<template>
    <div>
        <div class="bg-image">
            <div class="col px-30 pt-30 relative">
                <!-- <div class="relative inline-block">

                    <h1 class="glitchtext absolute -left-0.5 text-gray-400" data-text="ROBOT SOCCER">ROBOT <br> SOCCER
                    </h1>
                    <h1 class="glitchtext relative -left-0.5 text-black" data-text="ROBOT SOCCER">ROBOT <br> SOCCER</h1>

                </div> -->

                <div class="relative inline-block">
                    <span class="glitchtextfront pulse-effect">ROBOT <br> SOCCER</span>
                    <span class="glitchtextback pulse-effect">ROBOT <br> SOCCER</span>
                </div>

                <div class="pt-8 flex items-center">
                    <router-link to="/tv/levelselector">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=http://127.0.0.1:8000/"
                            alt="QR Code" class="h-60 w-60 p-10 bg-white">
                    </router-link>
                    <div class="ml-4">
                        <p class="text-white text-3xl">Connected:</p>
                        <p class="text-white text-3xl">{{ message }}</p>
                    </div>
                </div>

            </div>

        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            socket: null,
            message: null
        }
    },
    mounted() {
        this.socket = new WebSocket((process.env.NODE_ENV === "development" ? "ws://192.168.127.40:8000" : "ws://89.117.63.5:8000") + "/ws/tv/onloading");

        this.socket.onopen = () => {
            console.log('Connected to websocket');
        }

        // on message from server, set the this.message to the message
        this.socket.onmessage = (e) => {

            this.message = e.data;

            if (this.message === "2") {
                this.$router.push('/tv/levelselector');
            }
        }

    }
}

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Black+Ops+One&display=swap');

.bg-image {
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0.4) 20%, rgba(0, 0, 0, 0)), url('/robotsoccerbg.png');
    background-position: center;
    background-size: cover;
    height: 100vh;
}

.glitchtextback {
    font-family: 'Black Ops One', sans-serif;
    font-size: 12rem;
    position: relative;
    /* Base color */
    display: inline-block;
    color: #ffffff;
    line-height: 9rem;
    letter-spacing: 5px;

}

.glitchtextfront {
    font-family: 'Black Ops One', sans-serif;
    font-size: 12rem;
    position: absolute;
    /* Base color */
    display: inline-block;
    color: #222F75;
    line-height: 9rem;
    letter-spacing: 5px;
    left: -1rem;

}

@keyframes pulse-glitch {

    0%,
    100% {
        transform: scale(1);

    }

    50% {
        transform: scale(1.05);

    }
}

.pulse-effect {
    animation: pulse-glitch 1.5s infinite ease-in-out;
}
</style>