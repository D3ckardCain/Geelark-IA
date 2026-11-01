"""Herramientas técnicas opcionales; no intervienen en el control habitual."""


def collect(controller, config):
    remote = ("hostname; uptime; free -m; df -h /; ip -br a; systemctl is-active docker; "
              "sudo -n docker ps -a")
    try:
        controller.run(controller.ssh() + [config.target, remote], timeout=30)
    except Exception:
        controller.emit("Consulta Docker incompleta: puede requerir contraseña sudo.")
    controller.android_status()
    adb = controller.require("adb")
    controller.run([adb, "-s", config.serial, "shell",
                    "pidof system_server; getprop init.svc.zygote; getprop init.svc.servicemanager"])
    controller.run([adb, "-s", config.serial, "logcat", "-b", "crash", "-d", "-t", "100"])
