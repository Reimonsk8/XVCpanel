// XVCpanel - Bouncing Balls (Processing) - OSC controlled
import java.net.*;
import java.nio.*;

int W = 1920;
int H = 1080;

class Ball {
    float x, y, vx, vy, r, hue;
    Ball(float x, float y, float r, float h) {
        this.x = x; this.y = y; this.r = r; this.hue = h;
        float a = random(TWO_PI);
        float v = random(2, 8);
        vx = cos(a) * v;
        vy = sin(a) * v;
    }
}

ArrayList<Ball> balls;
OscIn osc;
float targetCount = 24;
float speed = 4.0;
float sizeScale = 1.0;

void settings() {
    size(1920, 1080);
}

void setup() {
    if (System.getenv("XVC_HEADLESS") != null) surface.setVisible(false);
    colorMode(HSB, 360, 100, 100, 100);
    noStroke();
    balls = new ArrayList<Ball>();
    for (int i = 0; i < (int) targetCount; i++) {
        balls.add(new Ball(random(width), random(height), random(8, 22), random(360)));
    }
    osc = new OscIn(9011);
}

void draw() {
    targetCount = constrain(osc.get("/balls/count", targetCount), 2.0, 200.0);
    speed = constrain(osc.get("/balls/speed", speed), 0.5, 12.0);
    sizeScale = constrain(osc.get("/balls/size", sizeScale), 0.3, 3.0);

    fill(0, 0, 0, 18);
    rect(0, 0, width, height);

    while (balls.size() < (int) targetCount) {
        balls.add(new Ball(random(width), random(height), random(8, 22), random(360)));
    }
    while (balls.size() > (int) targetCount) {
        balls.remove(balls.size() - 1);
    }

    for (int i = 0; i < balls.size(); i++) {
        Ball b = balls.get(i);
        b.vx *= 0.998;
        b.vy *= 0.998;
        b.x += b.vx * speed / 5.0;
        b.y += b.vy * speed / 5.0;
        if (b.x < b.r) { b.x = b.r; b.vx = abs(b.vx); }
        if (b.x > width - b.r) { b.x = width - b.r; b.vx = -abs(b.vx); }
        if (b.y < b.r) { b.y = b.r; b.vy = abs(b.vy); }
        if (b.y > height - b.r) { b.y = height - b.r; b.vy = -abs(b.vy); }
        fill(b.hue, 90, 90, 230);
        ellipse(b.x, b.y, b.r * 2 * sizeScale, b.r * 2 * sizeScale);
    }

    fill(0, 0, 100);
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) +
         "  Balls: " + balls.size() +
         "  Press F to fullscreen", 10, height - 10);

    snapshotToFrame();
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

long lastShot = 0;

// ~4 fps scaled PNG next to the sketch; the panel's [v] preview pane renders it
void snapshotToFrame() {
    if (millis() - lastShot < 250) {
        return;
    }
    lastShot = millis();
    new File(sketchPath("data")).mkdirs();
    PImage full = get();
    PImage small = createImage(320, 180, RGB);
    small.copy(full, 0, 0, width, height, 0, 0, 320, 180);
    small.save("data/frame.png");
}