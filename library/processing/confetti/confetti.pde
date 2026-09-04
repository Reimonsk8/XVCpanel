// XVCpanel - Confetti Bursts (Processing) - OSC controlled
import java.net.*;
import java.nio.*;

int W = 1920;
int H = 1080;

class Burst {
    float x, y, vx, vy, hue, life, size;
    Burst(float x, float y, float h, float s) {
        this.x = x; this.y = y; this.hue = h; this.size = s;
        float a = random(TWO_PI);
        float v = random(2, 10);
        vx = cos(a) * v;
        vy = sin(a) * v;
        life = 1.0;
    }
}

ArrayList<Burst> parts;
OscIn osc;
float rate = 8.0;
float gravity = 0.08;
float hueShift = 0.0;

void settings() {
    size(1920, 1080);
}

void setup() {
    colorMode(HSB, 360, 100, 100, 100);
    rectMode(CENTER);
    parts = new ArrayList<Burst>();
    osc = new OscIn(9010);
}

void draw() {
    rate = constrain(osc.get("/confetti/rate", rate), 0.5, 30.0);
    gravity = constrain(osc.get("/confetti/gravity", gravity), 0.0, 0.5);
    hueShift = osc.get("/confetti/hue", hueShift) % 360.0;

    fill(0, 0, 0, 14);
    noStroke();
    rect(width / 2, height / 2, width, height);

    if (random(1) < rate / 30.0) {
        parts.add(new Burst(random(width), random(height * 0.6), (hueShift + random(80)) % 360, random(3, 8)));
    }

    for (int i = parts.size() - 1; i >= 0; i--) {
        Burst b = parts.get(i);
        b.vy += gravity;
        b.x += b.vx;
        b.y += b.vy;
        b.life -= 0.015;
        if (b.life <= 0 || b.x < -20 || b.x > width + 20 || b.y > height + 20) {
            parts.remove(i);
            continue;
        }
        stroke(b.hue, 90, 100, b.life * 100);
        strokeWeight(b.size * b.life + 1);
        point(b.x, b.y);
    }

    fill(0, 0, 100);
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) +
         "  Confetti: " + parts.size() +
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