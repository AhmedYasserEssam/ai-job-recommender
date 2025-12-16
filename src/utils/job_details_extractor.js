function extractJobDetails() {
    const result = {
        experience: 'N/A',
        careerLevel: 'N/A',
        education: 'N/A',
        salary: 'N/A',
        categories: 'N/A',
        skills: 'N/A',
        requirements: 'N/A'
    };

    const jobDetailsH2 = Array.from(document.querySelectorAll('h2')).find(h => h.textContent.includes('Job Details'));
    if (jobDetailsH2) {
        const section = jobDetailsH2.parentElement;
        const allDivs = section.querySelectorAll('div');

        for (const div of allDivs) {
            const text = div.textContent.trim();

            if (text.startsWith('Experience Needed:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.experience = childText;
                        break;
                    }
                }
            }

            if (text.startsWith('Career Level:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.careerLevel = childText;
                        break;
                    }
                }
            }

            if (text.startsWith('Education Level:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.education = childText;
                        break;
                    }
                }
            }

            if (text.startsWith('Salary:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.salary = childText;
                        break;
                    }
                }
            }
        }

        const catLabel = Array.from(section.querySelectorAll('*')).find(el => 
            el.childNodes.length === 1 && el.textContent.trim() === 'Job Categories:'
        );
        if (catLabel) {
            const list = catLabel.nextElementSibling;
            if (list) {
                const cats = Array.from(list.querySelectorAll('a')).map(a => a.textContent.trim());
                result.categories = cats.length > 0 ? cats.join(' | ') : 'N/A';
            }
        }
    }

    const skillsHeading = Array.from(document.querySelectorAll('h4')).find(h => h.textContent.includes('Skills'));
    if (skillsHeading) {
        const container = skillsHeading.nextElementSibling;
        if (container) {
            const allSkills = Array.from(container.querySelectorAll('a')).map(a => a.textContent.trim());
            const uniqueSkills = [...new Set(allSkills)];
            result.skills = uniqueSkills.length > 0 ? uniqueSkills.join(' | ') : 'N/A';
        }
    }

    const reqHeading = Array.from(document.querySelectorAll('h2')).find(h => h.textContent.includes('Job Requirements'));
    if (reqHeading) {
        const reqSection = reqHeading.nextElementSibling;
        if (reqSection) {
            result.requirements = reqSection.textContent.trim().substring(0, 500) || 'N/A';
        }
    }

    return result;
}
