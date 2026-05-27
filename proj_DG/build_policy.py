import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))
        
        # Upper running rule
        self.setStrokeColor(colors.HexColor("#E5E5E5"))
        self.setLineWidth(0.5)
        self.line(54, 738, 558, 738)
        self.drawString(54, 746, "DIGITALKUBER SYSTEM ARCHITECTURE — INFORMATION SECURITY POLICY")
        
        # Bottom footer rule
        self.line(54, 54, 558, 54)
        self.drawString(54, 42, "CONFIDENTIAL — CORE OPERATIONAL COMPLIANCE BOUNDARY")
        self.drawRightString(558, 42, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def generate_aligned_policy(filename="DigiQuber_Information_Security_Policy.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=colors.HexColor("#111111"), spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, leading=15,
        textColor=colors.HexColor("#A48E56"), spaceAfter=20
    )
    
    h1_style = ParagraphStyle(
        'SectionH1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=13, leading=17,
        textColor=colors.HexColor("#111111"), spaceBefore=14, spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'PolicyBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=13.5,
        textColor=colors.HexColor("#333333"), spaceAfter=6
    )

    story.append(Paragraph("DigitalKuber", title_style))
    story.append(Paragraph("Information Security Policy — Full Cloud Architecture Mapping", subtitle_style))
    
    sections = [
        ("1. Edge Isolation, DNS & Boundary Protection", [
            "<b>DNS Domain Routing:</b> Public entry points to the application are restricted exclusively via <b>Amazon Route 53</b> configuration records.",
            "<b>DDoS & Bot Shielding:</b> Perimeter edge security uses integrated <b>AWS WAF & Shield</b> profiles to block malicious bot mutations, layer-7 exploits, and large-scale volumetric attacks prior to hitting compute target networks.",
            "<b>Edge Distribution Security:</b> Asset delivery is performance-isolated utilizing <b>Amazon CloudFront CDN</b> layers linked natively back to non-public object storage pools."
        ]),
        ("2. Transport Layer Security & Browser Constraints", [
            "<b>Wire Session Encryption:</b> External ingress endpoints terminate at an <b>AWS Application Load Balancer (ALB)</b> enforcing transport parameters. Internal processing links utilize strictly transport-forced TLS 1.3 connectivity protocols.",
            "<b>Strict Security Tokens:</b> State tokens rely on unique multi-factor validation strings. Internal partner handshakes execute using time-bounded <b>MMTC SessionID Cookies</b> configured with a hard 10-minute Time-To-Live (TTL) constraint to neutralize replay exposure vectors.",
            "<b>Database Cryptography:</b> Communications targeting backend microservices execute across port 6543 pool configurations under mandatory <i>'sslmode=require'</i> controls to defeat proxy interception risks."
        ]),
        ("3. Storage Isolation & Strict Scope Exclusions (PCI/DSS)", [
            "<b>Sensitive PII Controls:</b> Personally Identifiable Information (User Full Name, Verification Identities, Email, Mobile Parameters, Date of Birth, Address Data, and PAN/Aadhaar Reference Identifiers) is classified and sealed through <b>Supabase Managed PostgreSQL</b> architectures utilizing structural Row-Level Security (RLS) constraints.",
            "<b>Credit Card & Financial Scope Exclusion:</b> DigitalKuber explicitly mandates a **Zero-Storage** policy regarding card payment elements. Raw Credit Card Numbers, Expiry Parameter Sets, and Card Verification Values (CVV) are completely blocked from the application layer footprint. All payment lifecycles are processed off-site via tokens executed natively via **Razorpay Integration** hooks."
        ]),
        ("4. Operations Secrets Isolation & Config Management", [
            "<b>Zero Code-Level Credentials:</b> Hardcoded infrastructure credentials, database connectivity links, or vendor cryptographic tokens are strictly barred from checking into repository branches.",
            "<b>Central Storage Parameterization:</b> Runtime credentials (including database strings, Razorpay API connection variables, and internal token signing secrets) are stored remotely and encrypted via the <b>AWS Systems Manager (SSM) Parameter Store</b>, initialized dynamically via non-cached runtime retrieval wrappers."
        ]),
        ("5. Deployment Integrity, Pipeline Safety & Compute", [
            "<b>Compute Clusters Isolation:</b> Application processing logic maps down to containerized setups running on <b>Amazon EC2/ECS Compute Infrastructure clusters</b> powered via high-performance Gunicorn backend processing engines.",
            "<b>CI/CD Pipeline Security:</b> Code deployments execute automatically under strict multi-stage **GitHub Actions workflows**. Infrastructure mutations rely on secure, isolated SSH handshakes using programmatic deployment variables, eliminating persistence access loops."
        ]),
        ("6. Centralized Monitoring, Threat Audit & Logging", [
            "<b>Continuous Threat Detection:</b> Infrastructure environments are constantly scanned by <b>AWS GuardDuty</b> executing intelligent analytics to intercept potential compute layer compromises and malicious accounts manipulation.",
            "<b>Infrastructure & Application Metrics:</b> Deep container tracing, operating system loops, and operational alerts map into centralized tracking nodes via **Amazon CloudWatch** and **CloudWatch Alarms** linked directly to automated notification matrices.",
            "<b>System Auditing & Trail Persistence:</b> Every technical modification, programmatic execution script, and IAM account validation toggle is tracked, archived, and timestamped comprehensively through centralized <b>AWS CloudTrail</b> monitoring outputs to guarantee audit traceability."
        ])
    ]

    for title, texts in sections:
        section_flowables = [Paragraph(title, h1_style)]
        for paragraph in texts:
            section_flowables.append(Paragraph(paragraph, body_style))
        story.append(KeepTogether(section_flowables))
        story.append(Spacer(1, 4))
        
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Success: '{filename}' has been generated safely.")

if __name__ == "__main__":
    generate_aligned_policy()
