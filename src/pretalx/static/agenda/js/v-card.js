document.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('.participant-v-card').forEach((vCard) => {

        const downloadButton = vCard.querySelector('.participant-v-card__download-btn');
        downloadButton.addEventListener('click', e => {

            const givenName = vCard.querySelector('.first_name') ? vCard.querySelector('.first_name').textContent : '';
            const lastName = vCard.querySelector('.last_name') ? vCard.querySelector('.last_name').textContent : '';
            const organisation = vCard.querySelector('.org') ? vCard.querySelector('.org').textContent : '';
            const email = vCard.querySelector('.email') ? vCard.querySelector('.email').textContent : '';
            const postcode = vCard.querySelector('.postal-code') ? vCard.querySelector('.postal-code').textContent : '';
            const city = vCard.querySelector('.city') ? vCard.querySelector('.city').textContent : '';
            const country = vCard.querySelector('.country') ? vCard.querySelector('.country').textContent : '';

            // Constructing the vCard string
            let vCardString = `BEGIN:VCARD\n`;
            vCardString += `VERSION:3.0\n`;
            vCardString += `FN:${givenName} ${lastName}\n`;
            if (organisation) vCardString += `ORG:${organisation}\n`;
            if (email) vCardString += `EMAIL:${email}\n`;

            if (postcode || city || country) {
                const adrPostalCode = (postcode) ? postcode : '';
                const adrCity = (city) ? city : '';
                const adrCountry = (country) ? country : '';
                vCardString += `ADR:;;;${city};;${adrPostalCode};${adrCountry}\n`;
            }

            vCardString += `END:VCARD\n`;

            // Creating a Blob for the vCard
            const blob = new Blob([vCardString], { type: 'text/vcard' });
            const url = URL.createObjectURL(blob);

            // Creating an anchor element for the download
            const a = document.createElement('a');
            a.href = url;
            a.download = `${givenName}_${lastName}.vcf`; // Naming the vCard file
            document.body.appendChild(a);
            a.click(); // Trigger the download
            document.body.removeChild(a); // Clean up
            URL.revokeObjectURL(url); // Release the blob URL
        })
    })
})
