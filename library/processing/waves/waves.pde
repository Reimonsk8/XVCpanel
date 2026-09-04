// XVCpanel - Sine Waves (Processing) - OSC controlled
import java.net.*;
import java.nio.*;

int W = 1920;
int H = 1080;

OscIn osc;
float speed = 1.0;
float amplitude = 0.5;
float layers = 4.0;

void settings() {
    size(1920, 1080);
}

void setup() {
    colorMode(HSB, 360, 100, 100, 100);
    noFill();
    osc = new OscIn(9012);
}

void draw() {
    speed = constrain(osc.get("/waves/speed", speed), 0.1, 8.0);
    amplitude = constrain(osc.get("/waves/amp", amplitude), 0.05, 1.0);
    layers = constrain(osc.get("/waves/layers", layers), 1.0, 12.0);

    fill(0, 0, 0, 22);
    rect(0, 0, width, height);
    strokeWeight(2);

    int L = (int) layers;
    for (int l = 0; l < L; l++) {
        float baseY = (l + 0.5f) * height / L;
        float freq = 1.5 + l * 0.6;
        float phase = frameCount * 0.02 * speed + l * 0.7;
        float hu = (frameCount * 0.4 + l * 360.0 / max(L, 1)) % 360;
        stroke(hu, 80, 90, 200);
        beginShape();
        for (int x = 0; x <= width; x += 8) {
            float y = baseY + sin(x * TWO_PI / width * freq + phase) * amplitude * 120;
            vertex(x, y);
        }
        endShape();
    }

    fill(0, 0, 100);
    noStroke();
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) +
         "  Layers: " + L +
         "  Press F to fullscreen", 10, height - 10);
}

void keyPressed() {
    if (key == 'f' || key == 'F') {
        if (fullscreen) {
            surface.setSize(1920, 1080);
        } else {
            surface.setSize(displayWidth, displayHeight);
        }
        fullscreen = !fullscreen;
    }
    if (key == 'c' || key == 'C') {
        background(0);
    }
}

boolean fullscreen = false;

// --- minimal OSC receiver (background thread), no third-party lib ---
class OscIn extends Thread {
    DatagramSocket sock;
    java.util.Map<String, Float> vals = new java.util.HashMap<>();

    OscIn(int port) {
        try {
            sock = new DatagramSocket(port);
            start();
        } catch (Exception e) {
            println("OSC listen failed on " + port + ": " + e);
        }
    }

    public void run() {
        byte[] buf = new byte[512];
        while (sock != null && !sock.isClosed()) {
            try {
                DatagramPacket p = new DatagramPacket(buf, buf.length);
                sock.receive(p);
                String[] m = decode(buf, p.getLength());
                if (m != null) vals.put(m[0], Float.parseFloat(m[1]));
            } catch (Exception e) {
                // ignore partial/empty packets
            }
        }
    }

    float get(String addr, float def) {
        Float v;
        synchronized (vals) { v = vals.get(addr); }
        return v == null ? def : v;
    }

    String[] decode(byte[] b, int len) {
        int i = 0;
        String addr = "";
        while (i < len && b[i] != 0) { addr += (char) b[i]; i++; }
        if (addr.length() == 0) return null;
        i = (i + 4) & ~3;
        while (i < len && b[i] != 0) i++;
        i = (i + 4) & ~3;
        if (i + 4 > len) return null;
        ByteBuffer bb = ByteBuffer.wrap(b, i, 4).order(ByteOrder.BIG_ENDIAN);
        return new String[]{addr, Float.toString(bb.getFloat())};
    }
}