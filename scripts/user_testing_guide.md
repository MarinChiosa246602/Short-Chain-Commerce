# User Testing Guide

## Overview

This guide outlines the user testing procedures for the Short Chain Commerce Dashboard.

## Pre-Testing Setup

### 1. Environment Configuration
- Ensure backend API is running on port 8000
- Start frontend development server on port 3000
- Verify all services are healthy

### 2. Test Accounts
Create test scenarios with different user types:
- **Farm Operator**: Focuses on extraction accuracy
- **Warehouse Manager**: Focuses on batch processing
- **Quality Inspector**: Focuses on condition assessment

## Test Scenarios

### Scenario 1: First-Time User Onboarding
**Objective**: Evaluate ease of use for new users

**Tasks:**
1. Navigate to the dashboard
2. Upload an image for extraction
3. Review extraction results
4. Save or download results

**Success Criteria:**
- User completes all tasks without assistance
- Average time < 5 minutes
- Zero critical errors

### Scenario 2: Batch Processing
**Objective**: Test batch upload workflow

**Tasks:**
1. Navigate to extraction page
2. Select multiple images (5-10)
3. Process batch
4. Review aggregated results

**Success Criteria:**
- All images processed successfully
- Results properly aggregated
- Processing time within acceptable range

### Scenario 3: History and Search
**Objective**: Evaluate data retrieval

**Tasks:**
1. Navigate to history page
2. Search for specific extraction by ID
3. Filter by status
4. Export to CSV

**Success Criteria:**
- Search returns correct results
- Filters work as expected
- Export file is valid

### Scenario 4: Settings Configuration
**Objective**: Test configuration workflow

**Tasks:**
1. Navigate to settings
2. Modify extraction parameters
3. Save changes
4. Verify changes applied

**Success Criteria:**
- Changes persist after page reload
- Defaults work correctly
- No validation errors

## Usability Metrics

### Quantitative Measures
| Metric | Target | Measurement |
|--------|--------|-------------|
| Task Completion Rate | >90% | % of tasks completed |
| Time on Task | <5 min | Average time per task |
| Error Rate | <5% | Errors per session |
| Satisfaction Score | >4/5 | User rating |

### Qualitative Measures
- Ease of navigation
- Clarity of instructions
- Visual design preferences
- Feature requests

## Feedback Collection

### In-App Feedback
1. **Rating System**: Users can rate extractions (1-5 stars)
2. **Issue Reporting**: Select predefined issues
3. **Comments**: Open text feedback

### Session Recording
1. Enable testing mode in settings
2. Record user interactions
3. Export and analyze data

## Testing Checklist

### Pre-Test
- [ ] Environment setup complete
- [ ] Test scenarios documented
- [ ] Consent forms prepared
- [ ] Recording equipment ready

### During Test
- [ ] Instructions clear to participant
- [ ] Tasks performed without intervention
- [ ] Issues noted in real-time
- [ ] Session recorded (with consent)

### Post-Test
- [ ] Data exported and backed up
- [ ] Feedback analyzed
- [ ] Issues logged
- [ ] Improvement recommendations documented

## Common Issues & Solutions

### Issue: Extraction Takes Too Long
**Solution**: Optimize image preprocessing, enable GPU acceleration

### Issue: OCR Fails on Certain Images
**Solution**: Improve image enhancement, adjust confidence thresholds

### Issue: Navigation Confusion
**Solution**: Simplify menu structure, add tooltips

### Issue: Mobile Responsiveness Issues
**Solution**: Implement responsive breakpoints, test on devices

## Reporting Template

```
User Testing Report - [Date]

Participant: [ID]
Role: [User Type]
Duration: [Time]

Tasks Completed: [X/Y]
Issues Found: [List]
Satisfaction Score: [X/5]

Key Findings:
- [Finding 1]
- [Finding 2]

Recommendations:
- [Recommendation 1]
- [Recommendation 2]
```

## A/B Testing

### Test Variations
1. **Button Placement**: Left vs Right aligned
2. **Color Schemes**: Blue vs Green primary
3. **Layout**: Sidebar vs Top navigation

### Implementation
1. Create variant branches
2. Randomize user assignment
3. Track conversion metrics
4. Statistical analysis

## Accessibility Testing

### WCAG 2.1 Checklist
- [ ] Color contrast ratio > 4.5:1
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Focus indicators visible
- [ ] Alt text on images

### Tools
- axe DevTools
- WAVE
- Lighthouse
- Screen reader testing (NVDA, VoiceOver)
