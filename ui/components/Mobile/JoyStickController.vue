<template>
    <div class="flex flex-col items-center justify-center h-screen touch-none bg-black">
        <div class="flex w-full h-1/2">
            <div class="flex items-center justify-center w-1/2 h-full">
                <VueJoystick :size="300" :baseColor="'#999999'" :stickColor="'#666666'" :baseLineWidth="5"
                    :stickLineWidth="5" @move="handleJoystickMove" @start="handleJoystickStart"
                    @stop="handleJoystickEnd">
                </VueJoystick>
            </div>
            <div class="flex flex-wrap items-center justify-center w-1/2">
                <button v-for="button in buttons" :key="button.label"
                    class="w-32 h-32 m-4 text-4xl font-bold border-none rounded-full bg-blue-600 text-white cursor-pointer select-none touch-manipulation active:bg-blue-700"
                    @touchstart="handleButtonPress(button.label)" @touchend="handleButtonRelease(button.label)"
                    @mousedown="handleButtonPress(button.label)" @mouseup="handleButtonRelease(button.label)">
                    {{ button.label }}
                </button>
            </div>
        </div>
        <div class="text-center font-mono mt-8">
            <p>Joystick: {{ joystickOutput }}</p>
            <p>Buttons: {{ buttonsOutput }}</p>
        </div>
    </div>
</template>

<script>
import { Joystick } from 'vue-joystick-component';
export default {
    props: ['userid'],
    components: {
        VueJoystick: Joystick
    },
    data() {
        return {
            joystickOutput: 'Idle',
            buttonsOutput: [],
            robotcontrolsocket: null,
            buttons: [
                { label: 'CW' },
                { label: 'ACW' }
            ]
        };
    },
    methods: {
        handleJoystickMove(data) {
            const { x, y } = data;
            this.joystickOutput = `x: ${x.toFixed(2)}, y: ${y.toFixed(2)}`;
        },
        handleJoystickStart() {
            this.joystickOutput = 'Started';
        },
        handleJoystickEnd() {
            console.log("released")
            this.joystickOutput = { x: 0, y: 0 };
            if (this.robotcontrolsocket) {
                this.robotcontrolsocket.send(JSON.stringify({
                    type: 'joystick',
                    userid: this.userid,
                    joystick: this.joystickOutput
                }));
            }

        },
        handleButtonPress(label) {
            console.log(label)
            this.robotcontrolsocket.send(JSON.stringify({
                type: 'buttons',
                userid: this.userid,
                buttons: label
            }));
        },
        handleButtonRelease(label) {
            console.log("released")
            this.joystickOutput = { x: 0, y: 0 };
            if (this.robotcontrolsocket) {
                this.robotcontrolsocket.send(JSON.stringify({
                    type: 'joystick',
                    userid: this.userid,
                    joystick: this.joystickOutput
                }));
            }
        }
    },
    watch: {


        joystickOutput(newVal) {
            console.log(newVal)
            try {
                const x = newVal.split(',')[0].split(':')[1].trim();
                const y = newVal.split(',')[1].split(':')[1].trim();

                this.robotcontrolsocket.send(JSON.stringify({
                    type: 'joystick',
                    userid: this.userid,
                    joystick: {
                        x: parseFloat(x),
                        y: parseFloat(y)
                    }
                }));
            } catch (e) {
                console.log("Error parsing joystick output: ", e);
            }


        }
    },
    mounted() {

        this.robotcontrolsocket = new WebSocket((process.env.NODE_ENV === "development" ? "ws://192.168.127.40:8000" : "ws://89.117.63.5:8000") + "/ws/mobilecontrol");

        this.robotcontrolsocket.onopen = () => {
            console.log('Connected to websocket');
        }

        document.body.addEventListener(
            'touchmove',
            (e) => {
                e.preventDefault();
            },
            { passive: false }
        );
    }
};
</script>

<style scoped>
/* Removed CSS as it is now replaced with Tailwind classes */
</style>
