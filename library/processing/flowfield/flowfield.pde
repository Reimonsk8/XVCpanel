// XVCpanel — Flow Field
// Run with: processing-java --sketch=%CD% --run

int W = 1920;
int H = 1080;
int NUM_PARTICLES = 10000;
int COLS = 120;
int ROWS = 68;

float[][] flowField;
ArrayList<PVector> particles;
float zoff = 0;

void settings() {
    size(1920, 1080);
}

void setup() {
    background(0);
    flowField = new float[COLS * ROWS];
    particles = new ArrayList<PVector>();

    for (int i = 0; i < NUM_PARTICLES; i++) {
        particles.add(new PVector(random(width), random(height)));
    }

    colorMode(HSB, 360, 100, 100, 100);
}

void draw() {
    fill(0, 0, 0, 4);
    noStroke();
    rect(0, 0, width, height);

    // update flow field
    float xoff = 0;
    for (int x = 0; x < COLS; x++) {
        float yoff = 0;
        for (int y = 0; y < ROWS; y++) {
            float angle = noise(xoff, yoff, zoff) * TWO_PI * 2;
            flowField[x + y * COLS] = angle;
            yoff += 0.1;
        }
        xoff += 0.1;
    }
    zoff += 0.005;

    // update and draw particles
    for (int i = 0; i < particles.size(); i++) {
        PVector p = particles.get(i);

        int col = (int)(p.x / width * COLS);
        int row = (int)(p.y / height * ROWS);
        col = constrain(col, 0, COLS - 1);
        row = constrain(row, 0, ROWS - 1);

        float angle = flowField[col + row * COLS];
        PVector force = PVector.fromAngle(angle);
        force.mult(0.5);

        p.add(force);

        // wrap around
        if (p.x > width) p.x = 0;
        if (p.x < 0) p.x = width;
        if (p.y > height) p.y = 0;
        if (p.y < 0) p.y = height;

        // draw
        float hu = (angle / TWO_PI * 360 + frameCount * 0.5) % 360;
        stroke(hu, 80, 90, 40);
        point(p.x, p.y);
    }

    // HUD
    fill(0, 0, 100);
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) +
         "  Particles: " + NUM_PARTICLES +
         "  Flow: " + COLS + "x" + ROWS +
         "  Press F to fullscreen", 10, height - 10);
}

void mouseDragged() {
    // inject force at mouse
    int col = (int)(mouseX / width * COLS);
    int row = (int)(mouseY / height * ROWS);
    for (int dx = -2; dx <= 2; dx++) {
        for (int dy = -2; dy <= 2; dy++) {
            int c = constrain(col + dx, 0, COLS - 1);
            int r = constrain(row + dy, 0, ROWS - 1);
            flowField[c + r * COLS] = atan2(mouseY - (r * height / ROWS),
                                             mouseX - (c * width / COLS));
        }
    }
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
