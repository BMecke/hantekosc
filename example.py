import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from hantekosc import oscilloscope

osc = oscilloscope.Oscilloscope()
osc.channels[0].voltage_range = 5
osc.channels[1].voltage_range = 5
osc.trigger_mode = 'REPEAT'
osc.sample_rate = 1 * 1e6
osc.record_length = 100000
osc.pre_sample_ratio = 0.2
osc.channels[0].trigger_kind = 'FALLING'

osc.start()


delay_ = 0
case_ = 0

fig, ax = plt.subplots()
xdata, ydata = [], []
ln, = ax.plot([], [], 'b')




def init():
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return ln,


def update(frame):
    global delay_
    global case_

    x_data = osc.channels[0].measured_data[0]
    y_data = osc.channels[0].measured_data[1]

    """
    if delay_ == 20:
        match case_:
            case 0:
                osc.sample_rate = 50 * 1e3
            case 1:
                osc.sample_rate = 70 * 1e3
            case 3:
                osc.sample_rate = 100 * 1e3
            case 4:
                osc.sample_rate = 500 * 1e3
            case 5:
                osc.sample_rate = 24000 * 1e3
                case_ = 0

        delay_ = 0
        case_ += 1

    delay_ += 1
    """


    ln.set_data(x_data, y_data)

    x_min = min(x_data)
    x_max = max(x_data)
    x_scale = max([abs(x_min), abs(x_max)])
    y_min = min(y_data)
    y_max = max(y_data)
    y_scale = max([abs(y_min), abs(y_max)])

    ln.axes.set_xlim(min(x_data) - x_scale * 0.05, max(x_data) + x_scale * 0.05)
    ln.axes.set_ylim(min(y_data) - y_scale * 0.1, max(y_data) + y_scale * 0.05)
    return ln,

ani = FuncAnimation(fig, update, frames=10, init_func=init, blit=False)
plt.show()

osc.stop()
osc.scope.close_handle()



